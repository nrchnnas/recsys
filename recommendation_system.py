import sqlite3
import numpy as np
import pandas as pd
from collections import Counter
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

class DescriptionOnlyRecommender:
    """
    A book recommendation system that prioritizes:
    1. Similar books data (highest weight)
    2. Vector embedding of DESCRIPTION ONLY (medium weight)
    3. Genre matching (lowest weight)
    
    With support for single book title input
    """
    
    def __init__(self, db_path="books.db"):
        self.db_path = db_path
        self.conn = None
        self.df = None
        self.genre_columns = []
        self.text_vectorizer = None
        self.text_matrix = None
        
        # Vector embedding settings
        self.vector_max_features = 5000
        self.vector_min_df = 5
        self.vector_max_df = 0.5
        
        # Weights for different recommendation methods
        self.similar_books_weight = 0.1
        self.vector_embedding_weight = 0.7
        self.genre_weight = 0.2
    
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def load_data(self):
        """Load book data from the database."""
        if not self.conn:
            if not self.connect():
                return False
        
        try:
            # Select only the columns that we know exist in the database
            query = """
            SELECT book_id, title_without_series, authors, description, 
                   average_rating, ratings_count, genres, similar_books,
                   num_pages
            FROM books
            WHERE ratings_count > 20
            """
            
            print("Loading data from database...")
            start_time = time.time()
            self.df = pd.read_sql_query(query, self.conn)
            load_time = time.time() - start_time
            print(f"Loaded {len(self.df)} books in {load_time:.2f} seconds")
            
            # Create genre columns from the genres field
            print("Creating genre columns from 'genres' field...")
            self._create_genre_columns_from_genres()
            
            # Parse similar_books if it exists
            if "similar_books" in self.df.columns:
                print("Parsing similar books data...")
                start_time = time.time()
                self.df["similar_books_list"] = self.df["similar_books"].apply(self._parse_similar_books)
                # Count how many books have similar_books data
                has_similar = self.df["similar_books_list"].apply(lambda x: len(x) > 0)
                parse_time = time.time() - start_time
                print(f"Found {has_similar.sum()} books with similar_books data in {parse_time:.2f} seconds")
                
                # Create basic ID mappings for similar books matching
                self._create_basic_id_mappings()
            
            # Clean and prepare description field for vector embedding
            print("Preparing description data for vectorization...")
            self.df['clean_description'] = self.df['description'].fillna('')
            
            # Add basic "is_duplicate" flag for later filtering
            self.df['is_duplicate'] = False
            
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_genre_columns_from_genres(self):
        """Create binary genre columns from the 'genres' field."""
        if 'genres' not in self.df.columns:
            print("No 'genres' column found, cannot create genre columns")
            return
        
        # Parse the genres field - we know they're comma-separated
        def extract_genres(genres_str):
            if pd.isna(genres_str) or not genres_str:
                return []
            
            if isinstance(genres_str, str):
                return [genre.strip() for genre in genres_str.split(',') if genre.strip()]
            elif isinstance(genres_str, list):
                return genres_str
            
            return []
        
        # Extract all genres
        self.df['genre_list'] = self.df['genres'].apply(extract_genres)
        
        # Find the most common genres
        all_genres = []
        for genres in self.df['genre_list']:
            all_genres.extend(genres)
        
        genre_counter = Counter([g.lower() for g in all_genres if g])
        top_genres = [g for g, count in genre_counter.most_common(15) if count > 50]
        
        print(f"Found top genres: {top_genres}")
        
        # Create binary columns for top genres
        for genre in top_genres:
            safe_genre_name = re.sub(r'[^a-zA-Z0-9]', '_', genre.lower())
            column_name = f"is_{safe_genre_name}"
            self.df[column_name] = self.df['genre_list'].apply(
                lambda x: 1 if any(g.lower() == genre.lower() for g in x) else 0
            )
            self.genre_columns.append(column_name)
        
        print(f"Created {len(self.genre_columns)} genre columns")
    
    def _create_basic_id_mappings(self):
        """Create simple mappings to handle common book ID format issues."""
        # Create a simple mapping to handle string vs numeric IDs
        self.book_id_mapping = {}
        
        # Sample a subset for faster processing
        sample_size = min(5000, len(self.df))
        sample = self.df.sample(sample_size)
        
        for _, row in sample.iterrows():
            book_id = row['book_id']
            # Handle numeric IDs (some might be stored as strings)
            try:
                if isinstance(book_id, str) and book_id.isdigit():
                    self.book_id_mapping[int(book_id)] = book_id
            except:
                pass
    
    def prepare_vector_embeddings(self):
        """Create TF-IDF vector embeddings using only description field."""
        if self.df is None:
            if not self.load_data():
                return False
        
        print(f"Creating vector embeddings from descriptions (max_features={self.vector_max_features})...")
        start_time = time.time()
        
        # Remove books with empty descriptions for vectorization
        descriptions = self.df['clean_description']
        valid_descriptions = descriptions[descriptions != '']
        
        print(f"Found {len(valid_descriptions)} books with valid descriptions")
        
        # Sample texts for faster fitting (optional)
        sample_size = min(20000, len(valid_descriptions))
        if len(valid_descriptions) > sample_size:
            sample_indices = np.random.choice(valid_descriptions.index, size=sample_size, replace=False)
            sample_texts = valid_descriptions.loc[sample_indices]
        else:
            sample_texts = valid_descriptions
        
        # Create the TF-IDF vectorizer with reduced dimensions
        self.text_vectorizer = TfidfVectorizer(
            max_features=self.vector_max_features,
            min_df=self.vector_min_df,
            max_df=self.vector_max_df,
            stop_words='english'
        )
        
        # Fit on sample, transform all
        print("Fitting vectorizer on description sample...")
        self.text_vectorizer.fit(sample_texts)
        
        print("Transforming all book descriptions to vectors...")
        self.text_matrix = self.text_vectorizer.transform(self.df['clean_description'])
        
        vectorize_time = time.time() - start_time
        print(f"Created vector embeddings with shape: {self.text_matrix.shape} in {vectorize_time:.2f} seconds")
        
        return True
    
    def _normalize_book_id(self, book_id):
        """Convert book ID to canonical format."""
        return self.book_id_mapping.get(book_id, book_id)
    
    def _convert_to_int(self, value):
        """Convert various boolean representations to integers."""
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, (int, float)):
            return 1 if value > 0 else 0
        elif isinstance(value, str):
            if value.lower() in ('true', 't', 'yes', 'y', '1'):
                return 1
            else:
                return 0
        return 0
    
    def _parse_similar_books(self, similar_books_str):
        """Parse the similar_books string into a list of book IDs."""
        if pd.isna(similar_books_str) or not similar_books_str:
            return []
        
        try:
            # Try different parsing approaches based on the format
            if isinstance(similar_books_str, str):
                # Check if it's a JSON array
                if similar_books_str.startswith('[') and similar_books_str.endswith(']'):
                    try:
                        return json.loads(similar_books_str)
                    except:
                        pass
                
                # Check if it's comma-separated
                if ',' in similar_books_str:
                    return [book_id.strip() for book_id in similar_books_str.split(',') if book_id.strip()]
                
                # Single value
                return [similar_books_str.strip()]
            
            # It might already be a list
            elif isinstance(similar_books_str, list):
                return similar_books_str
        except:
            # Silently fail and return empty list
            pass
        
        return []
    
    def find_book(self, title=None, book_id=None):
        """Find a book by title or ID."""
        if self.df is None:
            if not self.load_data():
                return None
        
        if book_id:
            matches = self.df[self.df["book_id"] == book_id]
        elif title:
            # Case-insensitive partial match
            matches = self.df[self.df["title_without_series"].str.lower().str.contains(title.lower())]
        else:
            return None
        
        if len(matches) == 0:
            return None
        
        # Return the most popular match
        return matches.sort_values("ratings_count", ascending=False).iloc[0]
    
    def get_recommendations(self, book_id=None, title=None, num_recommendations=10):
        """
        Get book recommendations based on a given book, prioritizing:
        1. Similar books data (highest weight)
        2. Vector embedding similarity of description (medium weight)
        3. Genre matching (lowest weight)
        """
        if self.df is None:
            if not self.load_data():
                return pd.DataFrame()
        
        # Make sure we have vector embeddings
        if self.text_matrix is None:
            if not self.prepare_vector_embeddings():
                return pd.DataFrame()
        
        # Find the source book
        book = None
        if book_id:
            book = self.find_book(book_id=book_id)
        elif title:
            book = self.find_book(title=title)
        
        if book is None:
            print(f"Book not found: {title if title else book_id}")
            return pd.DataFrame()
        
        print(f"Finding recommendations for: {book['title_without_series']}")
        start_time = time.time()
        
        # Get source book's important info for filtering
        source_title = book['title_without_series']
        source_author = str(book['authors'])
        
        # Quick duplicate detection for source book's title
        def is_likely_duplicate(row):
            row_title = str(row['title_without_series']).lower()
            source_title_lower = str(source_title).lower()
            
            # If titles are too similar
            if source_title_lower == row_title:
                return True
                
            # Extract author IDs for comparison
            source_author_ids = set(re.findall(r'"author_id":\s*"([^"]+)"', source_author))
            row_author_ids = set(re.findall(r'"author_id":\s*"([^"]+)"', str(row['authors'])))
            
            # If same title and at least one author matches
            title_similar = (source_title_lower in row_title or row_title in source_title_lower)
            authors_match = bool(source_author_ids & row_author_ids)
            
            return title_similar and authors_match
        
        # Create filtered dataframe excluding the source book and likely duplicates
        # Use .copy() to avoid SettingWithCopyWarning
        filtered_df = self.df[
            (self.df['book_id'] != book['book_id']) & 
            (~self.df.apply(is_likely_duplicate, axis=1))
        ].copy()
        
        # 1. Score: Similar books (highest weight)
        if "similar_books_list" in self.df.columns and len(book.get("similar_books_list", [])) > 0:
            similar_ids = book["similar_books_list"]
            normalized_similar_ids = [self._normalize_book_id(id) for id in similar_ids]
            print(f"Book has {len(similar_ids)} explicitly listed similar books")
            
            # Add similar_books score efficiently
            similar_id_set = set(normalized_similar_ids)
            filtered_df['similar_books_score'] = filtered_df['book_id'].apply(
                lambda x: 1.0 if x in similar_id_set or self._normalize_book_id(x) in similar_id_set else 0.0
            )
            
            # Check how many similar books are in our database
            similar_books_count = filtered_df['similar_books_score'].sum()
            print(f"Found {int(similar_books_count)} similar books in our database")
        else:
            print("No similar books data available")
            filtered_df['similar_books_score'] = 0.0
        
        # 2. Score: Vector embedding similarity (based on description only)
        print("Calculating description similarity...")
        # Get the index of the source book
        book_idx = self.df[self.df['book_id'] == book['book_id']].index[0]
        
        # Only calculate similarity if source book has a description
        if book['clean_description']:
            # Calculate cosine similarity between the source book and all other books
            book_vector = self.text_matrix[book_idx]
            
            # Only calculate for filtered books to save time
            filtered_indices = filtered_df.index.tolist()
            filtered_matrix = self.text_matrix[filtered_indices]
            similarities = cosine_similarity(book_vector, filtered_matrix).flatten()
            
            # Assign similarity scores directly to the filtered dataframe
            filtered_df['vector_score'] = similarities
        else:
            print("Source book has no description, skipping description similarity")
            filtered_df['vector_score'] = 0.0
        
        # 3. Score: Genre matching
        print("Calculating genre similarity...")
        def calculate_genre_match(row):
            score = 0
            for col in self.genre_columns:
                if book[col] == 1 and row[col] == 1:
                    score += 1
            # Normalize by the number of genres the source book has
            source_genres = sum(book[col] for col in self.genre_columns)
            if source_genres > 0:
                return score / source_genres
            return 0
        
        filtered_df['genre_score'] = filtered_df.apply(calculate_genre_match, axis=1)
        
        # Calculate final weighted score
        filtered_df['final_score'] = (
            filtered_df['similar_books_score'] * self.similar_books_weight +
            filtered_df['vector_score'] * self.vector_embedding_weight +
            filtered_df['genre_score'] * self.genre_weight
        )
        
        # Sort by final score and get top recommendations
        recommendations = filtered_df.sort_values('final_score', ascending=False).head(num_recommendations).copy()
        
        # Add explanation of why books were recommended
        def get_recommendation_reason(row):
            reasons = []
            
            # Similar books match
            if row['similar_books_score'] > 0:
                reasons.append("Explicitly listed as similar")
            
            # Content similarity
            if row['vector_score'] > 0.2:  # Threshold for significant similarity
                reasons.append("Similar description")
            
            # Genre match
            if row['genre_score'] > 0:
                matching_genres = []
                for col in self.genre_columns:
                    if book[col] == 1 and row[col] == 1:
                        matching_genres.append(col.replace('is_', ''))
                
                if matching_genres:
                    reasons.append(f"Matching genres: {', '.join(matching_genres)}")
            
            if not reasons:
                return "General recommendation"
            
            return "; ".join(reasons)
        
        recommendations['recommendation_reason'] = recommendations.apply(get_recommendation_reason, axis=1)
        recommendations['source_book'] = book['title_without_series']  # Add source book info
        
        total_time = time.time() - start_time
        print(f"Generated recommendations in {total_time:.2f} seconds")
        
        return recommendations
    
    def print_recommendations(self, recommendations):
        """Print recommendations in a readable format."""
        if len(recommendations) == 0:
            print("No recommendations found")
            return
        
        print("\n=== Book Recommendations ===\n")
        
        # Print source book if that information is available
        if 'source_book' in recommendations.columns:
            source_book = recommendations['source_book'].iloc[0]
            print(f"Based on: {source_book}\n")
        
        for i, (_, book) in enumerate(recommendations.iterrows(), 1):
            print(f"{i}. {book['title_without_series']}")
            print(f"   Author: {book['authors']}")
            print(f"   Rating: {book['average_rating']} ({book['ratings_count']} ratings)")
            
            # Print scores if available
            if 'similar_books_score' in book:
                print(f"   Similar books score: {book['similar_books_score']:.2f}")
            if 'vector_score' in book:
                print(f"   Description similarity: {book['vector_score']:.2f}")
            if 'genre_score' in book:
                print(f"   Genre match: {book['genre_score']:.2f}")
            if 'final_score' in book:
                print(f"   Overall score: {book['final_score']:.2f}")
                
            # Print recommendation reason
            if 'recommendation_reason' in book:
                print(f"   Why: {book['recommendation_reason']}")
            
            if 'genres' in book and not pd.isna(book['genres']):
                print(f"   Genres: {book['genres']}")
                
            print()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")


# Example usage
if __name__ == "__main__":
    # Create recommender
    recommender = DescriptionOnlyRecommender("books.db")
    
    # Default number of recommendations
    num_recommendations = 5
    
    # Load data and prepare vectors
    recommender.load_data()
    recommender.prepare_vector_embeddings()
    
    # Get recommendations based on a single book title
    print("\n--- BOOK RECOMMENDATIONS ---")
    print(f"Showing top {num_recommendations} recommendations")
    
    book_title = input("Enter a book title: ")
    recommendations = recommender.get_recommendations(title=book_title, num_recommendations=num_recommendations)
    
    recommender.print_recommendations(recommendations)
    
    # Clean up
    recommender.close()