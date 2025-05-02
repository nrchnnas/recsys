import sqlite3
import numpy as np
import pandas as pd
from collections import Counter
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

class BalancedBookRecommender:
    """
    A balanced book recommendation system that prioritizes:
    1. Similar books data (highest weight)
    2. Vector embedding (lower dimension for speed)
    3. Genre matching (lowest weight)
    
    With optimizations for performance and fixes for pandas warnings
    """
    
    def __init__(self, db_path="books.db"):
        self.db_path = db_path
        self.conn = None
        self.df = None
        self.genre_columns = []
        self.text_vectorizer = None
        self.text_matrix = None
        
        # Vector embedding settings
        self.vector_max_features = 2000  # Reduced from 5000 to 2000
        self.vector_min_df = 5           # More aggressive filtering (from 2 to 5)
        self.vector_max_df = 0.5         # More aggressive filtering (from 0.85 to 0.5)
        
        # Weights for different recommendation methods
        self.similar_books_weight = 0.5
        self.vector_embedding_weight = 0.3
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
            # Select required columns
            query = """
            SELECT book_id, title_without_series, authors, description, 
                   average_rating, ratings_count, genres, similar_books,
                   is_children, is_comics_graphics, is_fantasy_paranormal, 
                   is_history_biography, is_mystery_thriller_crime, 
                   is_poetry, is_romance, is_young_adult
            FROM books
            WHERE ratings_count > 20
            """
            
            print("Loading data from database...")
            start_time = time.time()
            self.df = pd.read_sql_query(query, self.conn)
            load_time = time.time() - start_time
            print(f"Loaded {len(self.df)} books in {load_time:.2f} seconds")
            
            # Identify genre columns
            self.genre_columns = [col for col in self.df.columns if col.startswith('is_')]
            print(f"Found {len(self.genre_columns)} genre columns")
            
            # Convert genre columns to integers
            for col in self.genre_columns:
                self.df[col] = self.df[col].apply(self._convert_to_int)
            
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
            
            # Create combined text field for vector embedding
            print("Preparing text data for vectorization...")
            self.df['combined_text'] = self.df['title_without_series'].fillna('') + ' ' + self.df['description'].fillna('')
            
            # Add basic "is_duplicate" flag for later filtering
            self.df['is_duplicate'] = False
            
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
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
        """Create TF-IDF vector embeddings with reduced dimensionality."""
        if self.df is None:
            if not self.load_data():
                return False
        
        print(f"Creating vector embeddings (max_features={self.vector_max_features})...")
        start_time = time.time()
        
        # Sample texts for faster fitting (optional)
        sample_size = min(20000, len(self.df))  # Limit to 20,000 books for vocab building
        sample_indices = np.random.choice(len(self.df), size=sample_size, replace=False)
        sample_texts = self.df.iloc[sample_indices]['combined_text']
        
        # Create the TF-IDF vectorizer with reduced dimensions
        self.text_vectorizer = TfidfVectorizer(
            max_features=self.vector_max_features,  # Reduced dimensions 
            min_df=self.vector_min_df,              # Ignore uncommon terms
            max_df=self.vector_max_df,              # Ignore very common terms
            stop_words='english'
        )
        
        # Fit on sample, transform all
        print("Fitting vectorizer on text sample...")
        self.text_vectorizer.fit(sample_texts)
        
        print("Transforming all book texts to vectors...")
        self.text_matrix = self.text_vectorizer.transform(self.df['combined_text'])
        
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
        2. Vector embedding similarity (medium weight)
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
            
            # Check how many similar books are in our dataset
            similar_books_count = filtered_df['similar_books_score'].sum()
            print(f"Found {int(similar_books_count)} similar books in our database")
        else:
            print("No similar books data available")
            filtered_df['similar_books_score'] = 0.0
        
        # 2. Score: Vector embedding similarity
        print("Calculating content similarity...")
        # Get the index of the source book
        book_idx = self.df[self.df['book_id'] == book['book_id']].index[0]
        # Calculate cosine similarity between the source book and all other books
        book_vector = self.text_matrix[book_idx]
        
        # Only calculate for filtered books to save time
        filtered_indices = filtered_df.index.tolist()
        filtered_matrix = self.text_matrix[filtered_indices]
        similarities = cosine_similarity(book_vector, filtered_matrix).flatten()
        
        # Assign similarity scores directly to the filtered dataframe
        filtered_df['vector_score'] = similarities
        
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
                reasons.append("Similar content")
            
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
        
        total_time = time.time() - start_time
        print(f"Generated recommendations in {total_time:.2f} seconds")
        
        return recommendations
    
    def recommend_for_user(self, liked_books, num_recommendations=10):
        """Recommend books based on a list of books a user liked."""
        if self.df is None:
            if not self.load_data():
                return pd.DataFrame()
        
        # Make sure we have vector embeddings
        if self.text_matrix is None:
            if not self.prepare_vector_embeddings():
                return pd.DataFrame()
        
        # Find all books the user likes
        user_books = []
        for book in liked_books:
            if isinstance(book, str):
                # Assume it's a title
                found_book = self.find_book(title=book)
                if found_book is not None:
                    user_books.append(found_book)
            else:
                # Assume it's a book_id
                found_book = self.find_book(book_id=book)
                if found_book is not None:
                    user_books.append(found_book)
        
        if not user_books:
            print("None of the provided books were found")
            return pd.DataFrame()
        
        print(f"Found {len(user_books)} of your liked books")
        
        # Get recommendations for each book
        all_recommendations = []
        for book in user_books:
            book_recs = self.get_recommendations(book_id=book['book_id'], num_recommendations=5)
            if len(book_recs) > 0:
                all_recommendations.append(book_recs)
        
        if not all_recommendations:
            return pd.DataFrame()
        
        # Combine all recommendations
        combined_recommendations = pd.concat(all_recommendations).copy()
        
        # Remove books the user already likes
        user_book_ids = [book['book_id'] for book in user_books]
        combined_recommendations = combined_recommendations[~combined_recommendations['book_id'].isin(user_book_ids)]
        
        # Remove duplicates and count frequency
        combined_recommendations = combined_recommendations.drop_duplicates(subset=['book_id'])
        
        # Count how many source books recommended each book
        book_counts = Counter(combined_recommendations['book_id'])
        combined_recommendations['frequency'] = combined_recommendations['book_id'].apply(lambda x: book_counts[x])
        
        # Sort by frequency and then by average score
        result = combined_recommendations.sort_values(['frequency', 'final_score'], ascending=[False, False])
        
        return result.head(num_recommendations)
    
    def print_recommendations(self, recommendations):
        """Print recommendations in a readable format."""
        if len(recommendations) == 0:
            print("No recommendations found")
            return
        
        print("\n=== Book Recommendations ===\n")
        
        for i, (_, book) in enumerate(recommendations.iterrows(), 1):
            print(f"{i}. {book['title_without_series']}")
            print(f"   Author: {book['authors']}")
            print(f"   Rating: {book['average_rating']} ({book['ratings_count']} ratings)")
            
            # Print scores if available
            if 'similar_books_score' in book:
                print(f"   Similar books score: {book['similar_books_score']:.2f}")
            if 'vector_score' in book:
                print(f"   Content similarity: {book['vector_score']:.2f}")
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
    recommender = BalancedBookRecommender("books.db")
    
    # Load data and prepare vectors (with fewer dimensions)
    recommender.load_data()
    recommender.prepare_vector_embeddings()
    
    # Get recommendations for a specific book
    print("\n--- RECOMMENDATIONS BASED ON A BOOK ---")
    book_title = input("Enter a book title to get recommendations: ")
    recommendations = recommender.get_recommendations(title=book_title)
    recommender.print_recommendations(recommendations)
    
    
    # Clean up
    recommender.close()