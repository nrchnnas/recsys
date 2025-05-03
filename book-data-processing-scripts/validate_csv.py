import csv
import json
import os
from collections import defaultdict

def validate_csv_books(csv_file):
    """
    Validate a CSV file of books to ensure:
    1. No duplicate rows based on book_id
    2. All book_id entries in similar_books field refer to books in the CSV
    
    Args:
        csv_file: Path to the CSV file to validate
    """
    try:
        # Read the CSV file
        print(f"Reading CSV file: {csv_file}")
        
        # First pass: Build lookup dictionary and check for duplicates
        book_ids = set()
        duplicate_ids = set()
        book_id_to_row = {}
        row_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                row_count += 1
                
                # Get book_id
                book_id = row.get('book_id')
                if not book_id:
                    print(f"Warning: Row {row_count} has no book_id")
                    continue
                
                # Check for duplicate book_id
                if book_id in book_ids:
                    duplicate_ids.add(book_id)
                else:
                    book_ids.add(book_id)
                
                # Store row for later reference
                book_id_to_row[book_id] = row
        
        print(f"Read {row_count:,} rows containing {len(book_ids):,} unique book IDs")
        
        # Report duplicates
        if duplicate_ids:
            print(f"Found {len(duplicate_ids):,} duplicate book IDs:")
            for i, dup_id in enumerate(list(duplicate_ids)[:10]):  # Show first 10
                print(f"  - {dup_id}")
            if len(duplicate_ids) > 10:
                print(f"  (and {len(duplicate_ids) - 10} more...)")
        else:
            print("No duplicate book IDs found - good!")
        
        # Second pass: Check similar_books references
        missing_references = defaultdict(set)
        similar_books_format_issues = []
        
        for book_id, row in book_id_to_row.items():
            similar_books_data = row.get('similar_books', '[]')
            
            # Try to parse similar_books
            try:
                # First try direct parsing if already a list
                if isinstance(similar_books_data, list):
                    similar_books = similar_books_data
                # Otherwise parse as JSON string
                else:
                    similar_books = json.loads(similar_books_data)
            except (json.JSONDecodeError, TypeError):
                # Try cleaning and parsing again
                try:
                    # Replace single quotes with double quotes for JSON compatibility
                    if isinstance(similar_books_data, str):
                        similar_books_data = similar_books_data.replace("'", "\"")
                        similar_books = json.loads(similar_books_data)
                    else:
                        similar_books_format_issues.append((book_id, str(similar_books_data)[:50]))
                        similar_books = []
                except json.JSONDecodeError:
                    # Last resort - parse as comma-separated string
                    try:
                        if isinstance(similar_books_data, str):
                            similar_books_data = similar_books_data.strip('[]').replace('"', '').replace("'", "")
                            similar_books = [s.strip() for s in similar_books_data.split(',') if s.strip()]
                        else:
                            similar_books_format_issues.append((book_id, str(similar_books_data)[:50]))
                            similar_books = []
                    except Exception as e:
                        similar_books_format_issues.append((book_id, f"Error: {e}"))
                        similar_books = []
            
            # Check each similar book reference
            for similar_id in similar_books:
                if similar_id and similar_id not in book_ids:
                    missing_references[book_id].add(similar_id)
        
        # Report format issues
        if similar_books_format_issues:
            print(f"\nFound {len(similar_books_format_issues):,} books with similar_books format issues:")
            for i, (book_id, issue) in enumerate(similar_books_format_issues[:10]):  # Show first 10
                print(f"  - Book ID {book_id}: {issue}...")
            if len(similar_books_format_issues) > 10:
                print(f"  (and {len(similar_books_format_issues) - 10} more...)")
        else:
            print("\nNo similar_books format issues found - good!")
        
        # Report missing references
        if missing_references:
            print(f"\nFound {len(missing_references):,} books with references to missing books:")
            
            # Count total missing references
            total_missing = sum(len(refs) for refs in missing_references.values())
            print(f"Total of {total_missing:,} missing book references")
            
            # Show examples
            for i, (book_id, missing) in enumerate(list(missing_references.items())[:10]):  # Show first 10
                print(f"  - Book ID {book_id} references {len(missing)} missing books: {list(missing)[:5]}...")
            if len(missing_references) > 10:
                print(f"  (and {len(missing_references) - 10} more books with missing references...)")
        else:
            print("\nAll similar_books references are valid - good!")
        
        # Overall summary
        print("\nValidation Summary:")
        print(f"- Total rows: {row_count:,}")
        print(f"- Unique book IDs: {len(book_ids):,}")
        print(f"- Duplicate book IDs: {len(duplicate_ids):,}")
        print(f"- Books with format issues: {len(similar_books_format_issues):,}")
        print(f"- Books with missing references: {len(missing_references):,}")
        print(f"- Total missing references: {sum(len(refs) for refs in missing_references.values()) if missing_references else 0:,}")
        
    except Exception as e:
        import traceback
        print(f"Error during validation: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    # Change this to your CSV file path
    csv_file = "all_books_merged_50k.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
    else:
        validate_csv_books(csv_file)