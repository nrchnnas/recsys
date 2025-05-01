import sqlite3
import csv
import os
import re
from datetime import datetime

def clean_column_name(name):
    """
    Convert column names to valid SQLite column names.
    """
    # Replace any character that's not alphanumeric or underscore with underscore
    cleaned = re.sub(r'[^\w]', '_', name)
    # Ensure it doesn't start with a number
    if cleaned and cleaned[0].isdigit():
        cleaned = 'c_' + cleaned
    return cleaned.lower()

def determine_column_type(values):
    """
    Try to determine the best SQLite type for a column based on sample values.
    """
    if not values or all(v == '' or v is None for v in values):
        return 'TEXT'
    
    # Check for boolean values
    bool_values = {'true', 'false', 'yes', 'no', 't', 'f', 'y', 'n', '1', '0', True, False}
    if all(str(v).lower() in bool_values or v == '' or v is None for v in values):
        return 'BOOLEAN'
    
    # Check for integer values
    try:
        if all(v == '' or v is None or (str(v).strip() and int(str(v)) == float(str(v))) for v in values):
            return 'INTEGER'
    except (ValueError, TypeError):
        pass
    
    # Check for float values
    try:
        if all(v == '' or v is None or (str(v).strip() and float(str(v))) for v in values):
            return 'REAL'
    except (ValueError, TypeError):
        pass
    
    # Check for date values - this is a simple check, might need enhancement
    date_patterns = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{2}-\d{2}-\d{4}$'   # MM-DD-YYYY
    ]
    
    date_match = True
    for value in values:
        if value and value != '':
            value_matches = False
            for pattern in date_patterns:
                if re.match(pattern, str(value)):
                    value_matches = True
                    break
            if not value_matches:
                date_match = False
                break
    
    if date_match and any(values):
        return 'DATE'
    
    # Default to TEXT
    return 'TEXT'

def csv_to_sqlite(csv_file, db_file, table_name='books', sample_size=1000):
    """
    Create a SQLite database from a CSV file.
    
    Args:
        csv_file: Path to the CSV file
        db_file: Path to the SQLite database to create
        table_name: Name of the table to create
        sample_size: Number of rows to sample for column type detection
    """
    print(f"Starting conversion of {csv_file} to SQLite database {db_file}...")
    
    # Start timing
    start_time = datetime.now()
    
    # Read CSV header and sample some rows to determine column types
    column_samples = {}
    total_rows = 0
    
    # First pass: read headers and sample rows
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Clean column names for SQLite
        clean_headers = [clean_column_name(header) for header in headers]
        
        # Initialize samples
        column_samples = {header: [] for header in clean_headers}
        
        # Sample rows for type detection
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
                
            for j, value in enumerate(row):
                if j < len(clean_headers):  # Ensure we don't go out of bounds
                    column_samples[clean_headers[j]].append(value)
            
            total_rows = i + 1  # Track how many rows we've read
    
    # Determine column types
    column_types = {}
    for column, samples in column_samples.items():
        column_types[column] = determine_column_type(samples)
    
    # Create database and table
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Build CREATE TABLE statement
    columns_def = []
    for i, header in enumerate(clean_headers):
        col_type = column_types[header]
        columns_def.append(f'"{header}" {col_type}')
    
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns_def)})'
    
    print(f"Creating table with {len(clean_headers)} columns...")
    cursor.execute(create_table_sql)
    
    # Prepare for batch insertion
    placeholders = ', '.join(['?' for _ in clean_headers])
    insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
    
    # Second pass: insert all data
    print(f"Importing data from CSV...")
    batch_size = 5000
    batch = []
    rows_imported = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            # Pad row if needed
            padded_row = row + [''] * (len(clean_headers) - len(row))
            batch.append(padded_row[:len(clean_headers)])  # Ensure we don't exceed headers
            
            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                rows_imported += len(batch)
                print(f"Imported {rows_imported:,} rows...")
                batch = []
        
        # Insert any remaining rows
        if batch:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            rows_imported += len(batch)
    
    # Create indexes on commonly queried columns
    print("Creating indexes...")
    common_index_columns = ['book_id', 'title', 'authors', 'genres']
    
    for column in common_index_columns:
        clean_col = clean_column_name(column)
        if clean_col in clean_headers:
            try:
                index_name = f"idx_{table_name}_{clean_col}"
                cursor.execute(f'CREATE INDEX "{index_name}" ON "{table_name}" ("{clean_col}")')
                print(f"Created index on {clean_col}")
            except sqlite3.Error as e:
                print(f"Error creating index on {clean_col}: {e}")
    
    # Calculate and print statistics
    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    final_count = cursor.fetchone()[0]
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n--- Import Summary ---")
    print(f"Database: {db_file}")
    print(f"Table: {table_name}")
    print(f"Columns: {len(clean_headers)}")
    print(f"Rows imported: {final_count:,}")
    print(f"Duration: {duration:.2f} seconds")
    
    # Print database file size
    db_size_mb = os.path.getsize(db_file) / (1024 * 1024)
    print(f"Database size: {db_size_mb:.2f} MB")
    
    # Close connection
    conn.close()
    print("Done!")

if __name__ == "__main__":
    # Change these variables as needed
    input_file = "all_books_combined_200k.csv"  # Your CSV file
    output_db = "books.db"  # SQLite database to create
    table_name = "books"  # Table name to create
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
    else:
        csv_to_sqlite(input_file, output_db, table_name)
