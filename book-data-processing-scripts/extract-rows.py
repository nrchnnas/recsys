import json
import csv
import os
from collections import deque
from tqdm import tqdm  # For progress bar (optional, remove if not installed)

def extract_with_complete_similar_network(input_json, output_csv, initial_count=30000):
    """
    Extract books from JSON to CSV ensuring ALL similar book references are included.
    Implements a fully recursive network traversal to include all connected books.
    Removes references to books that don't exist in the input data.
    
    Args:
        input_json: Path to the input JSON file
        output_csv: Path to the output CSV file
        initial_count: Number of initial books to extract
    """
    try:
        # Load the JSON data
        print(f"Loading JSON data from {input_json}...")
        with open(input_json, 'r', encoding='utf-8') as f:
            try:
                # Try loading as a JSON array
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]  # Convert single object to list
            except json.JSONDecodeError:
                # Try loading as JSONL (one JSON object per line)
                data = []
                with open(input_json, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:  # Skip empty lines
                            try:
                                item = json.loads(line)
                                data.append(item)
                            except json.JSONDecodeError as e:
                                print(f"Warning: Skipping invalid JSON line: {e}")
        
        print(f"Loaded {len(data):,} books from JSON file")
        
        # Create a dictionary for fast lookups
        books_by_id = {}
        for book in data:
            book_id = book.get('book_id')
            if book_id:
                books_by_id[book_id] = book
        
        print(f"Created lookup dictionary with {len(books_by_id):,} book IDs")
        
        # Build complete similar book network
        print("Building complete similar book network...")
        similar_book_network = {}
        invalid_references_removed = 0
        
        # Parse and store all similar book relationships
        for book_id, book in books_by_id.items():
            similar_books_data = book.get('similar_books', [])
            similar_books = []
            
            # Parse similar books
            if isinstance(similar_books_data, str):
                try:
                    similar_books = json.loads(similar_books_data)
                except json.JSONDecodeError:
                    similar_books_data = similar_books_data.replace("'", "\"")
                    try:
                        similar_books = json.loads(similar_books_data)
                    except json.JSONDecodeError:
                        similar_books_data = similar_books_data.strip('[]').replace('"', '').replace("'", "")
                        similar_books = [s.strip() for s in similar_books_data.split(',') if s.strip()]
            else:
                similar_books = similar_books_data
            
            # Filter to only include existing book IDs
            original_count = len(similar_books)
            valid_similar_books = [s_id for s_id in similar_books if s_id in books_by_id]
            invalid_references_removed += (original_count - len(valid_similar_books))
            
            similar_book_network[book_id] = valid_similar_books
        
        print(f"Removed {invalid_references_removed:,} invalid references from similar_books")
        
        # Select initial books
        initial_books = []
        count = 0
        for book in data:
            book_id = book.get('book_id')
            if book_id and count < initial_count:
                initial_books.append(book_id)
                count += 1
            if count >= initial_count:
                break
        
        print(f"Selected {len(initial_books):,} initial books")
        
        # Traverse the network to include all connected books
        # This is a breadth-first search that will find ALL books connected to the initial set
        books_to_include = set()
        books_to_process = deque(initial_books)
        
        print("Finding all connected books in the network...")
        try:
            with tqdm(desc="Finding connected books") as pbar:
                while books_to_process:
                    current_book_id = books_to_process.popleft()
                    
                    # Skip if already processed
                    if current_book_id in books_to_include:
                        continue
                    
                    # Add this book to our set
                    books_to_include.add(current_book_id)
                    pbar.update(1)
                    
                    # Process all similar books
                    for similar_id in similar_book_network.get(current_book_id, []):
                        if similar_id not in books_to_include:
                            books_to_process.append(similar_id)
        except NameError:
            # If tqdm not available
            print("Processing without progress bar...")
            processed_count = 0
            
            while books_to_process:
                current_book_id = books_to_process.popleft()
                
                # Skip if already processed
                if current_book_id in books_to_include:
                    continue
                
                # Add this book to our set
                books_to_include.add(current_book_id)
                
                # Process all similar books
                for similar_id in similar_book_network.get(current_book_id, []):
                    if similar_id not in books_to_include:
                        books_to_process.append(similar_id)
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    print(f"Processed {processed_count:,} books, found {len(books_to_include):,} connected books")
        
        print(f"Identified {len(books_to_include):,} total books to include")
        
        # Determine CSV fields based on the first book
        if data:
            fields = list(data[0].keys())
        else:
            fields = []
        
        # Write the CSV file
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(fields)
            
            # Write data rows for all included books
            books_written = 0
            
            try:
                with tqdm(total=len(books_to_include), desc="Writing books to CSV") as pbar:
                    for book_id in books_to_include:
                        if book_id in books_by_id:
                            # Get the original book data
                            book = books_by_id[book_id]
                            
                            # Create a modified copy of the book with cleaned similar_books
                            book_copy = book.copy()
                            
                            # Replace the similar_books field with the cleaned version
                            # (already filtered for existence in the input JSON)
                            book_copy['similar_books'] = similar_book_network.get(book_id, [])
                            
                            # Prepare row
                            row = []
                            for field in fields:
                                value = book_copy.get(field, '')
                                # Convert lists, dicts, etc. to JSON strings
                                if not isinstance(value, (str, int, float)) and value is not None:
                                    value = json.dumps(value)
                                row.append(value)
                            
                            writer.writerow(row)
                            books_written += 1
                            pbar.update(1)
            except NameError:
                # If tqdm not available
                for book_id in books_to_include:
                    if book_id in books_by_id:
                        # Get the original book data
                        book = books_by_id[book_id]
                        
                        # Create a modified copy of the book with cleaned similar_books
                        book_copy = book.copy()
                        
                        # Replace the similar_books field with the cleaned version
                        # (already filtered for existence in the input JSON)
                        book_copy['similar_books'] = similar_book_network.get(book_id, [])
                        
                        # Prepare row
                        row = []
                        for field in fields:
                            value = book_copy.get(field, '')
                            # Convert lists, dicts, etc. to JSON strings
                            if not isinstance(value, (str, int, float)) and value is not None:
                                value = json.dumps(value)
                            row.append(value)
                        
                        writer.writerow(row)
                        books_written += 1
                        
                        if books_written % 1000 == 0:
                            print(f"Wrote {books_written:,} books to CSV")
        
        print(f"Successfully wrote {books_written:,} books to {output_csv}")
        print(f"Output file size: {os.path.getsize(output_csv) / (1024*1024):.2f} MB")
        
        # Verify that all references in the output are valid
        print("Verifying output integrity...")
        invalid_references = 0
        
        for book_id in books_to_include:
            if book_id in books_by_id:
                similar_books = similar_book_network.get(book_id, [])
                for similar_id in similar_books:
                    if similar_id not in books_to_include:
                        invalid_references += 1
        
        if invalid_references == 0:
            print("SUCCESS: All similar book references in output are valid!")
        else:
            print(f"WARNING: Found {invalid_references:,} invalid references in output")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    input_file = "goodreads_books_young_adult.json"  # Change to your input file
    output_file = "books_young_adult_30k.csv"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
    else:
        extract_with_complete_similar_network(input_file, output_file, 30000)