import pandas as pd

# Step 1: Load the datasets
print("Loading datasets...")
user_interactions = pd.read_csv('goodreads_interactions.csv')
all_books = pd.read_csv('all_books_merged_50k.csv')  # Adjust filename if needed

# Step 2: Get the set of valid book_ids from the all_books dataset
valid_book_ids = set(all_books['book_id'])

# Step 3: Apply both filters at once:
# - Keep only rows where is_read equals 1
# - Keep only rows where book_id is in the valid_book_ids set
filtered_interactions = user_interactions[
    (user_interactions['is_read'] == 1) & 
    (user_interactions['book_id'].isin(valid_book_ids))
]

# Step 4: Save the filtered data to a new CSV
filtered_interactions.to_csv('filtered_valid_interactions.csv', index=False)

# Step 5: Print statistics
print(f"Original interactions: {len(user_interactions)}")
print(f"After filtering:")
print(f"  - Valid interactions: {len(filtered_interactions)}")
print(f"  - Removed interactions: {len(user_interactions) - len(filtered_interactions)}")
print(f"  - is_read=1 count: {len(user_interactions[user_interactions['is_read'] == 1])}")
print(f"  - Valid book_ids count: {len(user_interactions[user_interactions['book_id'].isin(valid_book_ids)])}")
print("Filtering complete. Results saved to 'filtered_valid_interactions.csv'")