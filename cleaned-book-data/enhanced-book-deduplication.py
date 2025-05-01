import pandas as pd
import re
import argparse
from difflib import SequenceMatcher
import time

def clean_title(title):
    """
    Clean a book title by removing edition info, subtitles, and normalizing
    """
    if pd.isna(title):
        return ""
    
    # Remove text in parentheses (often edition info)
    title = re.sub(r'\(.*?\)', '', title)
    
    # Remove text after colon (often subtitles)
    title = re.sub(r':.*$', '', title)
    
    # Remove common edition markers
    edition_patterns = [
        r'(?i)illustrated edition', r'(?i)audiobook', r'(?i)kindle edition',
        r'(?i)paperback', r'(?i)hardcover', r'(?i)ebook', r'(?i)special edition',
        r'(?i)collector\'s edition', r'(?i)unabridged', r'(?i)abridged',
        r'(?i)anniversary edition', r'(?i)revised edition'
    ]
    for pattern in edition_patterns:
        title = re.sub(pattern, '', title)
    
    # Remove punctuation and extra spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    
    return title.strip().lower()

def extract_author_id(author_str):
    """Extract author IDs from the JSON-like author field"""
    if pd.isna(author_str):
        return frozenset()
    
    # Extract author_id values from JSON-like strings
    author_ids = re.findall(r'"author_id":\s*"([^"]+)"', str(author_str))
    return frozenset(author_ids)

def title_similarity(title1, title2):
    """Calculate similarity between two titles using SequenceMatcher"""
    if not title1 or not title2:
        return 0
    
    return SequenceMatcher(None, title1, title2).ratio() * 100

def deduplicate_books(input_file, output_file, similarity_threshold=85, 
                     prefer_highest_ratings=True, batch_size=5000):
    """
    Deduplicate books in a CSV file with batched processing and progress reporting
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        similarity_threshold: Title similarity threshold (0-100)
        prefer_highest_ratings: If True, keep the version with highest ratings_count
        batch_size: Size of batches for processing (for memory efficiency)
    """
    # Start timing
    start_time = time.time()
    
    print(f"Loading book dataset from {input_file}...")
    df = pd.read_csv(input_file)
    original_count = len(df)
    print(f"Loaded {original_count} books in {time.time() - start_time:.2f} seconds")
    
    # Step 1: Clean titles and extract author IDs
    print("Cleaning titles and extracting author IDs...")
    cleaning_start = time.time()
    df['clean_title'] = df['title_without_series'].apply(clean_title)
    df['author_ids'] = df['authors'].apply(extract_author_id)
    print(f"Cleaning completed in {time.time() - cleaning_start:.2f} seconds")
    
    # Step 2: Create initial grouping by first letter of title
    # This makes the duplicate detection much more efficient
    print("Creating initial title prefix groups...")
    df['title_prefix'] = df['clean_title'].apply(lambda x: x[:2] if x and len(x) >= 2 else '')
    
    # Step 3: Find duplicate groups within each prefix group
    print("Finding duplicate groups...")
    duplicate_groups = []
    
    total_prefixes = df['title_prefix'].nunique()
    processed_prefixes = 0
    
    # Get unique prefixes (excluding empty ones)
    prefixes = sorted([p for p in df['title_prefix'].unique() if p])
    
    grouping_start = time.time()
    for prefix in prefixes:
        # Get all books with this prefix
        prefix_group = df[df['title_prefix'] == prefix]
        
        if len(prefix_group) <= 1:
            continue
        
        # Find duplicates within this prefix group
        group_duplicates = []
        for i, (idx1, row1) in enumerate(prefix_group.iterrows()):
            # Skip if already in a group
            if any(idx1 in group for group in group_duplicates):
                continue
                
            current_group = [idx1]
            
            # Compare with remaining books in the group
            for idx2, row2 in list(prefix_group.iterrows())[i+1:]:
                # Check if authors match
                author_match = bool(row1['author_ids'] & row2['author_ids'])
                
                # If authors match, check title similarity
                if author_match:
                    sim = title_similarity(row1['clean_title'], row2['clean_title'])
                    if sim >= similarity_threshold:
                        current_group.append(idx2)
            
            if len(current_group) > 1:
                group_duplicates.append(current_group)
        
        # Add groups to main list
        duplicate_groups.extend(group_duplicates)
        
        # Update progress
        processed_prefixes += 1
        if processed_prefixes % 10 == 0 or processed_prefixes == total_prefixes:
            print(f"Processed {processed_prefixes}/{total_prefixes} prefix groups ({processed_prefixes/total_prefixes*100:.1f}%)")
    
    print(f"Found {len(duplicate_groups)} duplicate groups in {time.time() - grouping_start:.2f} seconds")
    
    # Step 4: Remove duplicates
    print("Selecting books to keep from duplicate groups...")
    indices_to_keep = set()
    
    for group_indices in duplicate_groups:
        # Extract the relevant group of books
        group_df = df.loc[group_indices]
        
        if prefer_highest_ratings:
            # Keep the version with the highest number of ratings
            max_ratings_idx = group_df['ratings_count'].idxmax()
            indices_to_keep.add(max_ratings_idx)
        else:
            # Just keep the first one
            indices_to_keep.add(group_indices[0])
    
    # Create a set of indices that are in duplicate groups
    duplicate_indices = set()
    for group in duplicate_groups:
        duplicate_indices.update(group)
    
    # Add all non-duplicate books
    for idx in df.index:
        if idx not in duplicate_indices:
            indices_to_keep.add(idx)
    
    # Create deduplicated dataframe
    deduplicated_df = df.loc[sorted(indices_to_keep)]
    
    # Remove temporary columns
    deduplicated_df = deduplicated_df.drop(['clean_title', 'author_ids', 'title_prefix'], axis=1)
    
    # Step 5: Save deduplicated dataset
    print(f"Saving deduplicated dataset to {output_file}...")
    deduplicated_df.to_csv(output_file, index=False)
    
    # Report results
    total_time = time.time() - start_time
    removed_count = original_count - len(deduplicated_df)
    print(f"Removed {removed_count} duplicate books ({removed_count/original_count*100:.1f}%)")
    print(f"Saved deduplicated dataset with {len(deduplicated_df)} books to {output_file}")
    print(f"Total processing time: {total_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description='Deduplicate a book dataset')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('output_file', help='Path to output CSV file')
    parser.add_argument('--similarity', type=int, default=85, 
                        help='Title similarity threshold (0-100)')
    parser.add_argument('--prefer-popular', action='store_true',
                        help='Prefer books with more ratings when removing duplicates')
    parser.add_argument('--batch-size', type=int, default=5000,
                        help='Size of batches for processing')
    
    args = parser.parse_args()
    
    deduplicate_books(
        args.input_file, 
        args.output_file,
        similarity_threshold=args.similarity,
        prefer_highest_ratings=args.prefer_popular,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main()
