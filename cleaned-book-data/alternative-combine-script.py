import json
import csv
import os
import re
from collections import defaultdict

def combine_json_to_csv(output_csv):
    """
    Combine all cleaned JSON files into a single CSV with proper genre handling.
    Uses book_id as the unique identifier and preserves all fields.
    """
    # Dictionary to store books by ID
    books_dict = {}
    
    # Track all genre names and all field names
    all_genres = set()
    all_fields = set()
    
    # Find all cleaned JSON files
    json_files = [f for f in os.listdir('.') if f.endswith('_short_cleaned.json')]
    print(f"Found {len(json_files)} JSON files to process")
    
    # First pass: collect all books and their fields
    for json_file in json_files:
        # Extract genre from filename (books_genre_short_cleaned.json)
        genre_match = re.search(r'books_(.+?)_short_cleaned\.json', json_file)
        if not genre_match:
            print(f"Skipping {json_file} - couldn't extract genre name")
            continue
            
        genre = genre_match.group(1)
        all_genres.add(genre)
        
        print(f"Processing {json_file} (genre: {genre})...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                books = json.load(f)
            
            for book in books:
                # Get unique identifier for the book
                book_id = str(book.get('book_id', ''))
                if not book_id:
                    # Fallback to title+author if no book_id
                    book_id = f"{book.get('title', '')}-{book.get('authors', '')}"
                
                # Update all_fields set
                for field in book.keys():
                    all_fields.add(field)
                
                # If this is a new book, add it to our dictionary
                if book_id not in books_dict:
                    books_dict[book_id] = book.copy()
                    books_dict[book_id]['genres'] = []
                
                # Add this genre to the book's genres
                if genre not in books_dict[book_id]['genres']:
                    books_dict[book_id]['genres'].append(genre)
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Add all genre fields to all_fields
    all_fields.add('genres')  # Combined genres field
    for genre in all_genres:
        all_fields.add(f"is_{genre}")  # Individual boolean fields
    
    # Convert to sorted list for consistent column order
    fieldnames = sorted(list(all_fields))
    
    print(f"Writing {len(books_dict)} unique books to CSV with {len(fieldnames)} columns")
    
    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for book_id, book in books_dict.items():
            # Create a row with all possible fields
            row = defaultdict(str)
            
            # Copy all existing book data
            for field, value in book.items():
                row[field] = value
            
            # Join genres into a comma-separated string
            row['genres'] = ', '.join(book['genres'])
            
            # Set boolean flags for each genre
            for genre in all_genres:
                row[f"is_{genre}"] = genre in book['genres']
            
            writer.writerow(row)
    
    print(f"Successfully created {output_csv}")
    print(f"Found {len(all_genres)} genres: {', '.join(sorted(all_genres))}")

if __name__ == "__main__":
    output_file = "all_books_combined.csv"
    combine_json_to_csv(output_file)
