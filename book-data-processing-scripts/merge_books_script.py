import pandas as pd
import os
import json
from collections import defaultdict
import random

# Define the genres (same as in clean-book-csvs.py)
GENRES = [
    "children",
    "comics_graphic",
    "fantasy_paranormal",
    "history_biography",
    "mystery_thriller_crime",
    "poetry",
    "romance",
    "young_adult"
]

def load_books_from_csv(file_path):
    """
    Load books from a CSV file, handling similar_books JSON properly
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='warn')
        
        # Parse similar_books column from JSON strings to Python lists
        if 'similar_books' in df.columns:
            def parse_similar_books(value):
                if pd.isna(value) or value == '[]' or value == '':
                    return []
                
                try:
                    # Try direct JSON parsing
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # Fix single quotes issue
                        if isinstance(value, str):
                            value = value.replace("'", "\"")
                            return json.loads(value)
                    except json.JSONDecodeError:
                        # Last resort - parse as comma-separated string
                        if isinstance(value, str):
                            value = value.strip('[]').replace('"', '').replace("'", "")
                            return [s.strip() for s in value.split(',') if s.strip()]
                return []
            
            df['similar_books'] = df['similar_books'].apply(parse_similar_books)
        
        # Add genre column based on file name
        genre = None
        for g in GENRES:
            if g in file_path:
                genre = g
                break
        
        if genre:
            df['genres'] = df.apply(lambda row: [genre], axis=1)
        
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def merge_book_csvs():
    """
    Merge all genre CSVs, combining genres for duplicate books and preserving similar_books references
    """
    print("Starting to merge book CSV files...")
    
    # Dictionary to hold all books by book_id
    all_books = {}
    
    # Process each genre
    for genre in GENRES:
        input_file = f"books_{genre}_30k_cleaned.csv"
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Input file {input_file} does not exist. Skipping.")
            continue
        
        print(f"Processing {input_file}...")
        df = load_books_from_csv(input_file)
        
        if df.empty:
            print(f"Failed to load {input_file} or file is empty. Skipping.")
            continue
        
        # Count books in this file
        book_count = len(df)
        print(f"  Loaded {book_count} books from {input_file}")
        
        # Process each book
        for _, row in df.iterrows():
            book_id = str(row['book_id'])
            
            if book_id in all_books:
                # Book already exists, merge genres
                if 'genres' in row and isinstance(row['genres'], list):
                    current_genres = all_books[book_id].get('genres', [])
                    new_genres = row['genres']
                    if not isinstance(current_genres, list):
                        current_genres = []
                    
                    # Combine genres without duplicates
                    combined_genres = list(set(current_genres + new_genres))
                    all_books[book_id]['genres'] = combined_genres
                
                # Merge similar_books lists (if any)
                if 'similar_books' in row and isinstance(row['similar_books'], list):
                    current_similar = all_books[book_id].get('similar_books', [])
                    new_similar = row['similar_books']
                    if not isinstance(current_similar, list):
                        current_similar = []
                    
                    # Combine similar_books without duplicates
                    all_books[book_id]['similar_books'] = list(set(current_similar + new_similar))
            else:
                # New book, add to dictionary
                book_dict = row.to_dict()
                all_books[book_id] = book_dict
    
    print(f"\nTotal unique books found across all genres: {len(all_books)}")
    
    # Convert genres from lists to comma-separated strings
    for book_id, book in all_books.items():
        if 'genres' in book and isinstance(book['genres'], list):
            book['genres'] = ','.join(book['genres'])
    
    # Create a DataFrame from the merged books
    merged_df = pd.DataFrame(list(all_books.values()))
    
    # Load all books first, then build a network of references
    # to ensure we include ALL necessary books
    print("\nBuilding complete book reference network...")
    
    # Create a directed graph of book references
    book_references = defaultdict(set)  # book_id -> set of books it references
    referenced_by = defaultdict(set)    # book_id -> set of books that reference it
    
    # Collect all references
    for book_id, book in all_books.items():
        similar_books = book.get('similar_books', [])
        if isinstance(similar_books, list):
            for ref_id in similar_books:
                book_references[book_id].add(ref_id)
                referenced_by[ref_id].add(book_id)
    
    # Identify all unique book_ids
    all_book_ids = set(all_books.keys())
    print(f"Total unique books: {len(all_book_ids)}")
    
    # Start with the first 50k books
    print(f"\nSelecting initial set of books...")
    book_ids_list = list(all_book_ids)
    initial_books = set(book_ids_list[:50000])
    print(f"Selected {len(initial_books)} initial books")
    
    # Find all referenced books that aren't in our initial set
    books_to_include = set(initial_books)
    pending_references = set()
    
    # Collect all books referenced by our initial set
    for book_id in initial_books:
        refs = book_references.get(book_id, set())
        pending_references.update(refs - books_to_include)
    
    # Keep adding references until we've captured the complete network
    iterations = 0
    while pending_references:
        iterations += 1
        print(f"Iteration {iterations}: Adding {len(pending_references)} referenced books...")
        
        # Add these books
        books_to_include.update(pending_references)
        
        # Find any new references from the books we just added
        new_refs = set()
        for book_id in pending_references:
            if book_id in book_references:
                new_refs.update(book_references[book_id] - books_to_include)
        
        # Update pending references for next iteration
        pending_references = new_refs
    
    print(f"Completed reference network after {iterations} iterations")
    print(f"Final selection includes {len(books_to_include)} books " + 
          f"({len(books_to_include) - len(initial_books)} additional books needed for complete reference integrity)")
    
    # Create a list of all book dictionaries to include
    selected_books = []
    for book_id in books_to_include:
        if book_id in all_books:
            selected_books.append(all_books[book_id])
        else:
            print(f"Warning: Referenced book ID {book_id} not found in original dataset")
    
    # Create a DataFrame from the selected books
    merged_df = pd.DataFrame(selected_books)
    print(f"Final dataset has {len(merged_df)} books")
    
    # Convert similar_books lists to JSON strings for CSV export
    if 'similar_books' in merged_df.columns:
        merged_df['similar_books'] = merged_df['similar_books'].apply(json.dumps)
    
    # Save the merged data
    output_file = "all_books_merged_50k.csv"
    merged_df.to_csv(output_file, index=False)
    print(f"\nSuccessfully saved merged data to {output_file}")
    
    # Verify all similar_books references point to existing books in the merged dataset
    verify_references(output_file)

def verify_references(csv_file):
    """
    Verify that all book_id references in similar_books exist in the dataset
    """
    print(f"\nVerifying book references in {csv_file}...")
    
    # Read the merged CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    # Get all book_ids in the dataset
    all_book_ids = set(df['book_id'].astype(str))
    print(f"Dataset contains {len(all_book_ids)} unique book IDs")
    
    # Parse similar_books and check references
    missing_references = 0
    total_references = 0
    
    for _, row in df.iterrows():
        book_id = str(row['book_id'])
        similar_books_data = row.get('similar_books', '[]')
        
        # Parse similar_books
        try:
            similar_books = json.loads(similar_books_data)
        except (json.JSONDecodeError, TypeError):
            # Try cleaning and parsing again
            try:
                # Replace single quotes with double quotes for JSON compatibility
                if isinstance(similar_books_data, str):
                    similar_books_data = similar_books_data.replace("'", "\"")
                    similar_books = json.loads(similar_books_data)
                else:
                    similar_books = []
            except json.JSONDecodeError:
                # Last resort - parse as comma-separated string
                if isinstance(similar_books_data, str):
                    similar_books_data = similar_books_data.strip('[]').replace('"', '').replace("'", "")
                    similar_books = [s.strip() for s in similar_books_data.split(',') if s.strip()]
                else:
                    similar_books = []
        
        # Check if all references exist
        for similar_id in similar_books:
            total_references += 1
            if similar_id not in all_book_ids:
                missing_references += 1
    
    if missing_references > 0:
        print(f"WARNING: Found {missing_references} missing references out of {total_references} total")
        print(f"Reference integrity: {100 - (missing_references / total_references * 100):.2f}%")
    else:
        print(f"All {total_references} book references are valid - excellent!")

if __name__ == "__main__":
    merge_book_csvs()