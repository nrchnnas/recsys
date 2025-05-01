import json
import csv
import os

# Fields to remove
fields_to_remove = [
    "kindle_asin",
    "asin",
    "language_code",
    "edition_information"
]

# File paths - change these if needed
input_file = "goodreads_books.json"
output_file = "books_cleaned.csv"

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, input_file)

print(f"Processing books from: {input_path}")

# Process the file
books = []
skipped_lines = 0

with open(input_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        try:
            # Parse the JSON object from this line
            book = json.loads(line)
            
            # Remove unwanted fields
            for field in fields_to_remove:
                if field in book:
                    book.pop(field, None)
            
            # Convert lists to JSON strings for CSV compatibility
            for field in ['authors', 'popular_shelves', 'series', 'similar_books']:
                if field in book and isinstance(book[field], list):
                    book[field] = json.dumps(book[field])
            
            books.append(book)
            
            # Print progress every 1000 books
            if len(books) % 1000 == 0:
                print(f"Processed {len(books)} books...")
                
        except json.JSONDecodeError as e:
            print(f"Warning: Skipping invalid JSON on line {line_num}")
            skipped_lines += 1

# If we didn't get any books, exit
if not books:
    print("Error: No valid book records found!")
    exit(1)

print(f"Successfully processed {len(books)} books. Skipped {skipped_lines} invalid lines.")

# Get all field names from all books
all_fields = set()
for book in books:
    all_fields.update(book.keys())

# Create the CSV
output_path = os.path.join(script_dir, output_file)
print(f"Writing CSV to: {output_path}")

with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=sorted(all_fields))
    writer.writeheader()
    writer.writerows(books)

print(f"Success! Removed {len(fields_to_remove)} fields from {len(books)} books.")
print(f"CSV file saved at: {output_path}")