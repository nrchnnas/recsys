import pandas as pd
import os

# Define the genres
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

# Fields to remove
FIELDS_TO_REMOVE = [
    "isbn", 
    "text_reviews_count", 
    "country_code", 
    "language_code", 
    "popular_shelves",
    "asin", 
    "is_ebook", 
    "kindle_asin", 
    "format", 
    "link", 
    "publisher", 
    "publication_day", 
    "title", 
    "isbn13", 
    "publication_month", 
    "edition_information", 
    "publication_year", 
    "url", 
    "image_url", 
    "work_id",
    "series"
]

def clean_csv_file(input_file, output_file):
    """
    Cleans the CSV file by:
    1. Removing rows where country_code is not "US"
    2. Removing specified columns
    """
    print(f"Processing {input_file}...")
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file, encoding='utf-8', on_bad_lines='warn')
        
        # Check if country_code column exists
        if 'country_code' in df.columns:
            # Filter for US only
            print(f"  Original row count: {len(df)}")
            df = df[df['country_code'] == 'US']
            print(f"  Row count after filtering for US only: {len(df)}")
        else:
            print(f"  Warning: 'country_code' column not found in {input_file}")
        
        # Remove specified fields if they exist
        columns_to_remove = [col for col in FIELDS_TO_REMOVE if col in df.columns]
        df = df.drop(columns=columns_to_remove, errors='ignore')
        
        print(f"  Removed {len(columns_to_remove)} columns")
        print(f"  Remaining columns: {', '.join(df.columns)}")
        
        # Save the cleaned data
        df.to_csv(output_file, index=False)
        print(f"  Successfully saved cleaned data to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return False

def main():
    print("Starting CSV cleanup process...")
    
    success_count = 0
    failure_count = 0
    
    # Process each genre
    for genre in GENRES:
        input_file = f"books_{genre}_30k.csv"
        output_file = f"books_{genre}_30k_cleaned.csv"
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Input file {input_file} does not exist. Skipping.")
            failure_count += 1
            continue
        
        if clean_csv_file(input_file, output_file):
            success_count += 1
        else:
            failure_count += 1
    
    print("\nProcessing complete.")
    print(f"Successful files: {success_count}")
    print(f"Failed/skipped files: {failure_count}")

if __name__ == "__main__":
    main()
