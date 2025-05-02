import csv
import os
from tqdm import tqdm  # For progress bar (optional, remove if not installed)

def cut_rows_from_csv(input_csv, output_csv, rows_to_keep):  # Changed to 200000
    """
    Extract the first N rows from a CSV file.
    
    Args:
        input_csv: Path to the input CSV file
        output_csv: Path to the output CSV file
        rows_to_keep: Number of rows to keep (default: 200000)  # Changed comment
    """
    try:
        # Get total row count first (for progress bar)
        total_rows = sum(1 for _ in open(input_csv, 'r', encoding='utf-8'))
        print(f"Total rows in input file: {total_rows:,}")
        
        # Check if we're keeping all rows
        if rows_to_keep >= total_rows:
            print(f"The file only has {total_rows:,} rows, which is less than the {rows_to_keep:,} rows you want to keep.")
            print("Creating a copy of the original file...")
            rows_to_keep = total_rows - 1  # Keep all but header row
        
        # Read the input file and write the first N rows to the output file
        with open(input_csv, 'r', encoding='utf-8') as infile, \
             open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # First, get the header row
            header = next(reader)
            writer.writerow(header)
            
            # Use tqdm for a progress bar if available
            try:
                # Write the first N rows
                for i, row in tqdm(enumerate(reader), total=rows_to_keep, desc="Processing rows"):
                    if i < rows_to_keep:
                        writer.writerow(row)
                    else:
                        break
            except NameError:
                # If tqdm is not installed, use a simpler approach
                print("Processing rows...")
                for i, row in enumerate(reader):
                    if i < rows_to_keep:
                        writer.writerow(row)
                    else:
                        break
                    # Simple progress indicator
                    if i % 50000 == 0:
                        print(f"Processed {i:,} rows...")
        
        print(f"Successfully wrote {rows_to_keep:,} rows to {output_csv}")
        print(f"Output file size: {os.path.getsize(output_csv) / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_file = "all_books_combined_100k.csv"
    output_file = "all_books_combined_50k.csv"  # Changed filename to reflect 200k
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
    else:
        cut_rows_from_csv(input_file, output_file, 50000)  # Changed to 200000