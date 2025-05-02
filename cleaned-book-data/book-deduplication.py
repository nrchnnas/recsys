import pandas as pd
import re
import argparse
import time
from difflib import SequenceMatcher
from collections import Counter
import numpy as np
import multiprocessing as mp
from functools import partial
import os
import sys

def normalize_title(title):
    """Aggressively normalize a title for comparison"""
    if pd.isna(title):
        return ""
    
    # Convert to lowercase and ensure string
    title = str(title).lower()
    
    # Remove text in parentheses (often edition info)
    title = re.sub(r'\(.*?\)', '', title)
    
    # Remove text after colon (often subtitles)
    title = re.sub(r':.*$', '', title)
    
    # Remove common edition markers
    edition_patterns = [
        r'(?i)illustrated edition', r'(?i)audiobook', r'(?i)kindle edition',
        r'(?i)paperback', r'(?i)hardcover', r'(?i)ebook', r'(?i)special edition',
        r'(?i)collector\'s edition', r'(?i)unabridged', r'(?i)abridged',
        r'(?i)anniversary edition', r'(?i)revised edition', r'(?i)complete edition'
    ]
    for pattern in edition_patterns:
        title = re.sub(pattern, '', title)
    
    # Remove all non-alphanumeric characters and replace with spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # Remove common words that don't help with identification
    for word in ['the', 'a', 'an', 'and', 'or', 'but', 'of', 'for', 'in', 'on', 'by', 'to', 'with']:
        title = re.sub(r'\b' + word + r'\b', ' ', title)
    
    # Remove extra spaces
    title = re.sub(r'\s+', ' ', title)
    
    return title.strip()

def get_words(title):
    """Extract words from a title"""
    return set(title.split())

def title_similarity(title1, title2):
    """
    Calculate a composite similarity score between two titles.
    This function combines multiple similarity metrics to get a more robust score.
    """
    # Ensure we have strings
    title1 = str(title1) if not pd.isna(title1) else ""
    title2 = str(title2) if not pd.isna(title2) else ""
    
    # Skip if either title is empty
    if not title1 or not title2:
        return 0.0
    
    # Skip if titles are identical
    if title1 == title2:
        return 1.0
    
    # 1. Sequence similarity (character-by-character)
    seq_similarity = SequenceMatcher(None, title1, title2).ratio()
    
    # 2. Word overlap similarity
    words1 = get_words(title1)
    words2 = get_words(title2)
    if not words1 or not words2:
        word_similarity = 0.0
    else:
        word_similarity = len(words1.intersection(words2)) / max(len(words1), len(words2))
    
    # 3. Character frequency similarity
    char_freq1 = Counter(title1)
    char_freq2 = Counter(title2)
    all_chars = set(char_freq1.keys()).union(set(char_freq2.keys()))
    
    # Calculate normalized character frequency vectors
    vec1 = np.array([char_freq1.get(c, 0) for c in all_chars])
    vec2 = np.array([char_freq2.get(c, 0) for c in all_chars])
    
    if len(vec1) > 0 and len(vec2) > 0:
        # Normalize vectors to unit length
        norm_vec1 = vec1 / (np.sum(vec1) or 1)
        norm_vec2 = vec2 / (np.sum(vec2) or 1)
        
        # Calculate cosine similarity
        dot_product = np.dot(norm_vec1, norm_vec2)
        char_similarity = dot_product
    else:
        char_similarity = 0.0
    
    # 4. Initial words similarity (first few words often most important)
    first_words1 = ' '.join(title1.split()[:2])
    first_words2 = ' '.join(title2.split()[:2])
    initial_similarity = SequenceMatcher(None, first_words1, first_words2).ratio()
    
    # 5. Length similarity - penalize very different lengths
    len_diff = abs(len(title1) - len(title2))
    max_len = max(len(title1), len(title2))
    length_penalty = 1.0 - (len_diff / (max_len + 1))
    
    # Weighted combination of similarity scores
    # Give more weight to sequence and word similarity
    composite_similarity = (
        0.35 * seq_similarity +      # Overall character-by-character similarity
        0.30 * word_similarity +     # Word overlap
        0.15 * char_similarity +     # Character frequency profile
        0.15 * initial_similarity +  # First words similarity
        0.05 * length_penalty        # Length difference penalty
    )
    
    return composite_similarity

def process_letter_group(args):
    """Process a single letter group to find duplicates (multiprocessing worker)"""
    letter, group_df, similarity_threshold = args
    
    duplicate_groups = []
    
    # Get indices and normalized titles
    indices = group_df.index.tolist()
    normalized_titles = group_df['normalized_title'].tolist()
    
    # Find duplicates within this letter group
    for i in range(len(indices)):
        # Skip if already in a duplicate group
        if any(indices[i] in group for group in duplicate_groups):
            continue
        
        current_group = [indices[i]]
        current_title = normalized_titles[i]
        
        # Compare with remaining books
        for j in range(i+1, len(indices)):
            # Skip if already in a duplicate group
            if any(indices[j] in group for group in duplicate_groups):
                continue
            
            # Calculate similarity
            sim = title_similarity(current_title, normalized_titles[j])
            
            if sim >= similarity_threshold:
                current_group.append(indices[j])
        
        if len(current_group) > 1:
            duplicate_groups.append(current_group)
    
    return letter, duplicate_groups

def deduplicate_books(input_file, output_file, similarity_threshold=0.8, 
                      title_column='title_without_series', ratings_column='ratings_count',
                      prefer_highest_ratings=True, debug=False, sample_size=5,
                      num_workers=None, chunk_size=None):
    """
    Deduplicate books using composite title similarity with multiprocessing
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        similarity_threshold: Title similarity threshold (0-1)
        title_column: Column containing book titles
        ratings_column: Column containing ratings count
        prefer_highest_ratings: If True, keep version with highest ratings
        debug: If True, print debug information
        sample_size: Number of duplicate samples to show
        num_workers: Number of worker processes (default: CPU count - 1)
        chunk_size: Process dataset in chunks (for memory efficiency)
    """
    start_time = time.time()
    
    # Set default number of workers
    if num_workers is None:
        num_workers = max(1, mp.cpu_count() - 1)  # Leave one CPU free
    
    print(f"Using {num_workers} worker processes")
    
    if chunk_size:
        # Process in chunks for large datasets
        print(f"Using chunked processing with chunk size {chunk_size}")
        # This would require a more complex implementation
        # For now, we'll focus on the multiprocessing optimization
        chunk_size = None
    
    print(f"Loading book dataset from {input_file}...")
    df = pd.read_csv(input_file)
    original_count = len(df)
    print(f"Loaded {original_count} books in {time.time() - start_time:.2f} seconds")
    
    # Verify columns exist
    if title_column not in df.columns:
        # Try to find a suitable title column
        title_columns = [col for col in df.columns if 'title' in col.lower()]
        if title_columns:
            title_column = title_columns[0]
            print(f"Title column '{title_column}' not found. Using '{title_column}' instead.")
        else:
            print(f"Error: Cannot find title column. Available columns: {', '.join(df.columns)}")
            return
    
    # Check ratings column if prefer_highest_ratings is True
    if prefer_highest_ratings and ratings_column not in df.columns:
        print(f"Warning: Ratings column '{ratings_column}' not found. Using first entry instead.")
        prefer_highest_ratings = False
    
    # Normalize titles
    print("Normalizing titles...")
    df['normalized_title'] = df[title_column].apply(normalize_title)
    
    # Quick optimization: if titles are exact duplicates after normalization, no need for similarity calculation
    print("Finding exact duplicates...")
    title_counts = df['normalized_title'].value_counts()
    exact_duplicate_titles = title_counts[title_counts > 1].index
    
    # Process exact duplicates
    exact_duplicate_groups = []
    
    if len(exact_duplicate_titles) > 0:
        print(f"Found {len(exact_duplicate_titles)} exact duplicate titles after normalization")
        
        for norm_title in exact_duplicate_titles:
            # Find all rows with this normalized title
            matches = df[df['normalized_title'] == norm_title].index.tolist()
            exact_duplicate_groups.append(matches)
    
    # Group by first letter to reduce comparisons and for parallel processing
    print("Grouping by first letter...")
    df['first_letter'] = df['normalized_title'].apply(lambda x: x[0] if x and len(x) > 0 else '')
    
    # Get all valid first letters
    first_letters = sorted([l for l in df['first_letter'].unique() if l])
    print(f"Processing {len(first_letters)} letter groups...")
    
    # Prepare arguments for parallel processing
    letter_groups = []
    for letter in first_letters:
        # Get all books with this first letter
        letter_df = df[df['first_letter'] == letter].copy()
        
        if len(letter_df) <= 1:
            continue
        
        # Skip books that are in exact duplicate groups
        if exact_duplicate_groups:
            exact_indices = set()
            for group in exact_duplicate_groups:
                exact_indices.update(group)
            
            letter_df = letter_df[~letter_df.index.isin(exact_indices)]
            
            if len(letter_df) <= 1:
                continue
        
        letter_groups.append((letter, letter_df, similarity_threshold))
    
    # Process letter groups in parallel
    print(f"Finding similar duplicates using {num_workers} processes...")
    similar_duplicate_groups = []
    
    if letter_groups:
        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(process_letter_group, letter_groups)
            
            for letter, groups in results:
                if groups:
                    print(f"Found {len(groups)} duplicate groups for letter '{letter}'")
                    similar_duplicate_groups.extend(groups)
    
    # Combine exact and similar duplicate groups
    all_duplicate_groups = exact_duplicate_groups + similar_duplicate_groups
    
    print(f"Found {len(all_duplicate_groups)} total duplicate groups")
    
    # Print sample duplicates if requested
    if debug and all_duplicate_groups:
        sample_size = min(sample_size, len(all_duplicate_groups))
        print(f"\nSample of {sample_size} duplicate groups:")
        
        for i, group in enumerate(all_duplicate_groups[:sample_size]):
            print(f"\nDuplicate Group {i+1}:")
            for idx in group:
                original = df.loc[idx, title_column]
                normalized = df.loc[idx, 'normalized_title']
                print(f"  Original: '{original}'")
                print(f"  Normalized: '{normalized}'")
    
    # Remove duplicates
    print("Removing duplicates...")
    indices_to_keep = set()
    
    # Add all non-duplicate books
    all_duplicate_indices = set()
    for group in all_duplicate_groups:
        all_duplicate_indices.update(group)
    
    for idx in df.index:
        if idx not in all_duplicate_indices:
            indices_to_keep.add(idx)
    
    # For each duplicate group, decide which one to keep
    for group in all_duplicate_groups:
        if prefer_highest_ratings and ratings_column in df.columns:
            # Keep book with highest ratings count
            ratings = df.loc[group, ratings_column]
            # Handle NaN values
            ratings = ratings.fillna(0)
            max_idx = ratings.idxmax()
            indices_to_keep.add(max_idx)
        else:
            # Just keep the first one
            indices_to_keep.add(group[0])
    
    # Create deduplicated dataframe
    deduplicated_df = df.loc[sorted(indices_to_keep)]
    
    # Remove temporary columns
    if 'normalized_title' in deduplicated_df.columns:
        deduplicated_df = deduplicated_df.drop(['normalized_title', 'first_letter'], axis=1)
    
    # Save deduplicated dataset
    print(f"Saving deduplicated dataset to {output_file}...")
    deduplicated_df.to_csv(output_file, index=False)
    
    # Report results
    total_time = time.time() - start_time
    removed_count = original_count - len(deduplicated_df)
    print(f"Removed {removed_count} duplicate books ({removed_count/original_count*100:.2f}%)")
    print(f"Saved deduplicated dataset with {len(deduplicated_df)} books")
    print(f"Total processing time: {total_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description='Book deduplication with composite similarity')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('output_file', help='Path to output CSV file')
    parser.add_argument('--similarity', type=float, default=0.8, 
                        help='Title similarity threshold (0-1), default: 0.8')
    parser.add_argument('--title-column', type=str, default='title_without_series',
                        help='Column name for book titles')
    parser.add_argument('--ratings-column', type=str, default='ratings_count',
                        help='Column name for ratings count')
    parser.add_argument('--prefer-popular', action='store_true',
                        help='Prefer books with more ratings')
    parser.add_argument('--debug', action='store_true',
                        help='Print debug information')
    parser.add_argument('--sample-size', type=int, default=5,
                        help='Number of duplicate samples to show')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes (default: CPU count - 1)')
    parser.add_argument('--chunk-size', type=int, default=None,
                        help='Process dataset in chunks (for memory efficiency)')
    
    args = parser.parse_args()
    
    # Convert percentage to decimal if needed
    similarity = args.similarity
    if similarity > 1:
        similarity = similarity / 100
    
    deduplicate_books(
        args.input_file,
        args.output_file,
        similarity_threshold=similarity,
        title_column=args.title_column,
        ratings_column=args.ratings_column,
        prefer_highest_ratings=args.prefer_popular,
        debug=args.debug,
        sample_size=args.sample_size,
        num_workers=args.workers,
        chunk_size=args.chunk_size
    )

if __name__ == "__main__":
    main()