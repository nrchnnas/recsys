import sqlite3
import pandas as pd
import os
import json
import re

def csv_to_sqlite(csv_file, db_file):
    """
    Convert CSV file to SQLite database, reinitializing the database each time.
    Ensures special characters are handled properly to avoid BLOB storage.
    
    Args:
        csv_file: Path to the input CSV file
        db_file: Path to the output SQLite database file
    """
    print(f"Converting {csv_file} to SQLite database {db_file}...")
    
    try:
        # Remove existing database file if it exists
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database file: {db_file}")
        
        # Read the CSV file
        print("Reading CSV file...")
        df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='warn')
        
        print(f"Found {len(df)} rows and {len(df.columns)} columns")
        
        # Connect to SQLite database
        print("Connecting to SQLite database...")
        conn = sqlite3.connect(db_file)
        
        # Set explicit UTF-8 encoding
        cursor = conn.cursor()
        cursor.execute("PRAGMA encoding = 'UTF-8'")
        
        # Set text_factory to ensure proper text handling
        conn.text_factory = str
        
        # Get column names and types
        print("Analyzing column data types...")
        column_info = []
        
        for column in df.columns:
            # Determine SQLite data type based on pandas dtype
            dtype = df[column].dtype
            
            if column == 'book_id':
                # Make book_id the primary key
                sql_type = "INTEGER PRIMARY KEY"
            elif pd.api.types.is_integer_dtype(dtype):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "REAL"
            elif column == 'similar_books':
                # Store JSON as TEXT
                sql_type = "TEXT"
            else:
                sql_type = "TEXT"
                
            column_info.append((column, sql_type))
        
        # Create table with appropriate schema
        print("Creating books table...")
        
        # Build the CREATE TABLE statement
        columns_def = ', '.join([f'"{col}" {dtype}' for col, dtype in column_info])
        create_table_sql = f"CREATE TABLE books ({columns_def})"
        
        # Execute the CREATE TABLE statement
        cursor.execute(create_table_sql)
        
        # Process data for insertion
        print("Processing data for insertion...")
        
        # Clean text columns to handle special characters
        for column, sql_type in column_info:
            if sql_type == 'TEXT':
                # Clean and sanitize text data
                df[column] = df[column].apply(
                    lambda x: clean_text(x) if pd.notna(x) else ""
                )
        
        # Process similar_books column (convert to JSON string if not already)
        if 'similar_books' in df.columns:
            df['similar_books'] = df['similar_books'].apply(
                lambda x: json.dumps(x) if not isinstance(x, str) else x
            )
        
        # Insert data row by row (more robust than pd.to_sql for complex data)
        print("Inserting data into database...")
        inserted_count = 0
        
        for _, row in df.iterrows():
            # Prepare data for insertion
            values = []
            for column in df.columns:
                value = row[column]
                
                # Convert NaN to None for SQLite
                if pd.isna(value):
                    value = None
                    
                values.append(value)
            
            # Create placeholders for the SQL query
            placeholders = ', '.join(['?' for _ in range(len(df.columns))])
            
            # Build the INSERT statement
            columns_str = ', '.join([f'"{col}"' for col in df.columns])
            insert_sql = f"INSERT INTO books ({columns_str}) VALUES ({placeholders})"
            
            try:
                # Execute the INSERT statement
                cursor.execute(insert_sql, values)
                inserted_count += 1
                
                # Commit every 10,000 rows to avoid memory issues
                if inserted_count % 10000 == 0:
                    conn.commit()
                    print(f"  {inserted_count} rows inserted...")
            except sqlite3.IntegrityError as e:
                print(f"Integrity error inserting book_id {row.get('book_id')}: {e}")
                # Continue with the next row
        
        # Final commit
        conn.commit()
        
        # Create an index on the book_id column for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_id ON books (book_id)")
        
        # Create an index on the average_rating column for faster sorting
        if 'average_rating' in df.columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_avg_rating ON books (average_rating)")
        
        # Create an index on the ratings_count column
        if 'ratings_count' in df.columns:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_count ON books (ratings_count)")
        
        conn.commit()
        
        # Verify the data was inserted correctly
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        print(f"\nVerification: Database contains {count} rows")
        
        if count != len(df):
            print(f"Warning: Row count mismatch. CSV has {len(df)} rows, database has {count} rows.")
        
        # Verify text columns are stored correctly
        print("Verifying text column storage types:")
        for column, sql_type in column_info:
            if sql_type == 'TEXT':
                cursor.execute(f"SELECT typeof({column}) FROM books LIMIT 1")
                actual_type = cursor.fetchone()
                if actual_type:
                    print(f"  Column '{column}' is stored as: {actual_type[0]}")
        
        # Close the connection
        conn.close()
        
        print(f"Successfully converted {csv_file} to SQLite database {db_file}")
        
    except Exception as e:
        import traceback
        print(f"Error during conversion: {e}")
        print(traceback.format_exc())
        return False
    
    return True

def clean_text(text):
    """
    Clean and sanitize text to ensure it's properly stored in SQLite.
    Handles special characters and removes invalid byte sequences.
    """
    if text is None:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Remove control characters that can cause issues
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
    
    return text

if __name__ == "__main__":
    input_file = "all_books_merged_50k.csv"  # Change to your input CSV file
    output_file = "books.db"  # Change to your desired DB file name
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
    else:
        csv_to_sqlite(input_file, output_file)