import json
import os

def fix_json_file(input_file, output_file):
    """Attempts to fix malformed JSON files by reading them line by line"""
    try:
        # First try to read and parse normally
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                print(f"JSON file {input_file} is already valid.")
                return data
            except json.JSONDecodeError:
                print(f"JSON file {input_file} is invalid. Attempting to fix...")
        
        # If that fails, read the file as text and try to identify and fix issues
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Common fix: if there are multiple JSON objects separated by newlines
        # Try to wrap them in an array
        if content.strip().startswith('{') and '\n{' in content:
            print("Detected multiple JSON objects. Attempting to wrap in array...")
            # Split by newline and filter out empty lines
            parts = [part for part in content.split('\n') if part.strip()]
            # Join with commas and wrap in array brackets
            fixed_content = '[' + ','.join(parts) + ']'
            try:
                data = json.loads(fixed_content)
                print("Successfully fixed by wrapping objects in array.")
                # Save the fixed JSON
                with open(output_file + '.fixed', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return data
            except json.JSONDecodeError as e:
                print(f"Fix attempt failed: {e}")
        
        # If we can't fix it, raise an exception
        raise ValueError(f"Could not fix JSON file {input_file}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return None

def remove_unwanted_fields(input_file, output_file):
    """Remove unwanted fields from a JSON file"""
    try:
        # Try to read the JSON file, with automatic fixing if needed
        data = fix_json_file(input_file, input_file)
        
        if data is None:
            print(f"Skipping {input_file} due to errors.")
            return
        
        # Fields to remove
        fields_to_remove = [
            "isbn", "text_reviews_count", "country_code", "language_code", "popular_shelves",
            "asin", "is_ebook", "kindle_asin", "format", "link", "publisher", "publication_day",
            "isbn13", "publication_month", "edition_information", "publication_year", "url",
            "image_url", "work_id"
        ]
        
        # Function to remove unwanted fields from an item
        def clean_item(item):
            if isinstance(item, dict):
                for field in fields_to_remove:
                    item.pop(field, None)
            return item
        
        # Process based on data structure
        if isinstance(data, list):
            # If data is a list of items
            cleaned_data = [clean_item(item) for item in data]
        elif isinstance(data, dict):
            # If data is a dictionary
            cleaned_data = {}
            for key, value in data.items():
                if isinstance(value, list):
                    # If value is a list of items
                    cleaned_data[key] = [clean_item(item) for item in value]
                else:
                    # Copy other values
                    cleaned_data[key] = value
            # Check if the main dictionary itself has unwanted fields
            cleaned_data = clean_item(cleaned_data)
        else:
            cleaned_data = data
        
        # Write the cleaned data back to a file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2)
        
        print(f"Successfully removed unwanted fields and saved to {output_file}")
    
    except Exception as e:
        print(f"Error processing {input_file}: {e}")

GENRES = [
    "children",
    "comics_graphics",
    "fantasy_paranormal",
    "history_biography",
    "mystery_thriller_crime",
    "poetry",
    "romance",
    "young_adult"
]

# Main function to remove unwanted fields from all genres
def main():
    print("Starting JSON cleanup process...")
    
    # Process each genre
    for genre in GENRES:
        input_file = f"books_{genre}_short.json"
        output_file = f"books_{genre}_short_cleaned.json"
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Input file {input_file} does not exist. Skipping.")
            continue
            
        print(f"Processing {input_file}...")
        remove_unwanted_fields(input_file, output_file)
    
    print("Processing complete.")

# This ensures the main() function runs when the script is executed directly
if __name__ == "__main__":
    main()