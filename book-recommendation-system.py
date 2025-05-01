import sqlite3
import numpy as np
import pandas as pd
from collections import Counter
import json

class SimilarFirstRecommender:
    """A book recommendation system that prioritizes explicitly similar books."""
    
    def __init__(self, db_path="books.db"):
        self.db_path = db_path
        self.conn = None
        self.df = None
        self.genre_columns = []
    
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def get_column_names(self):
        """Get the actual column names from the database."""
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(books)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Found {len(columns)} columns in the books table")
            return columns
        except Exception as e:
            print(f"Error getting column names: {e}")
            return []
    
    def load_data(self):
        """Load book data into a pandas DataFrame with flexible column handling."""
        if not self.conn:
            if not self.connect():
                return False
        
        # Get actual column names
        available_columns = self.get_column_names()
        
        # These are the columns we want if they exist
        desired_columns = [
            "book_id", "title_without_series", "authors", "average_rating", 
            "num_pages", "ratings_count", "genres", "series", "similar_books"
        ]
        
        # Expected genre columns with corrected naming
        expected_genre_columns = [
            "is_children", "is_comics_graphics", "is_fantasy_paranormal", 
            "is_history_biography", "is_mystery_thriller_crime", 
            "is_poetry", "is_romance", "is_young_adult"
        ]
        
        # Check which genre columns exist (starting with "is_")
        self.genre_columns = [col for col in available_columns if col.startswith("is_")]
        print(f"Found genre columns: {self.genre_columns}")
        
        # Build query with columns that actually exist
        columns_to_select = [col for col in desired_columns if col in available_columns]
        columns_to_select.extend(self.genre_columns)
        
        if not columns_to_select:
            print("Error: No valid columns found in database")
            return False
        
        # Create the SELECT query
        columns_str = ", ".join(columns_to_select)
        query = f"""
        SELECT {columns_str}
        FROM books
        WHERE ratings_count > 20
        """
        
        try:
            self.df = pd.read_sql_query(query, self.conn)
            print(f"Loaded {len(self.df)} books with {len(self.df.columns)} columns")
            
            # Convert genre columns to integers
            for col in self.genre_columns:
                self.df[col] = self.df[col].apply(self._convert_to_int)
            
            # Parse similar_books if it exists
            if "similar_books" in self.df.columns:
                self.df["similar_books_list"] = self.df["similar_books"].apply(self._parse_similar_books)
                # Count how many books have similar_books data
                has_similar = self.df["similar_books_list"].apply(lambda x: len(x) > 0)
                print(f"Found {has_similar.sum()} books with similar_books data")
            else:
                print("No similar_books column found in database")
            
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
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
        except Exception as e:
            print(f"Error parsing similar_books: {e}")
        
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
    
    def recommend_similar_books(self, book_id=None, title=None, num_recommendations=10):
        """
        Recommend books based on a given book, prioritizing the similar_books field.
        """
        if self.df is None:
            if not self.load_data():
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
        
        print(f"Finding recommendations similar to: {book['title_without_series']} by {book['authors']}")
        
        # PRIORITY 1: Check for explicitly similar books
        similar_books_df = pd.DataFrame()
        if "similar_books_list" in self.df.columns and len(book.get("similar_books_list", [])) > 0:
            similar_ids = book["similar_books_list"]
            print(f"Book has {len(similar_ids)} explicitly listed similar books")
            
            # Get books that are in our database
            similar_books_df = self.df[self.df["book_id"].isin(similar_ids)]
            print(f"Found {len(similar_books_df)} of these similar books in our database")
            
            # Sort by rating
            similar_books_df = similar_books_df.sort_values("average_rating", ascending=False)
            
            # If we have enough explicitly similar books, return them
            if len(similar_books_df) >= num_recommendations:
                print("Returning explicitly similar books")
                return similar_books_df.head(num_recommendations)
        
        # PRIORITY 2: Get genre-based recommendations
        genre_recs = self.recommend_by_genre_match(book, num_recommendations)
        
        # Combine explicit similar books with genre recommendations, removing duplicates
        if len(similar_books_df) > 0:
            # Combine the two dataframes, prioritizing the similar books
            combined_recs = pd.concat([similar_books_df, genre_recs])
            # Remove duplicates, keeping the first occurrence (from similar_books)
            combined_recs = combined_recs.drop_duplicates(subset=["book_id"])
            print("Returning combination of explicitly similar books and genre matches")
            return combined_recs.head(num_recommendations)
        
        # If no similar books were found, just return genre recommendations
        print("Returning genre-based recommendations")
        return genre_recs
    
    def recommend_by_genre_match(self, book, num_recommendations=10):
        """Recommend books with similar genres to the given book."""
        if not self.genre_columns:
            # If we don't have genre columns, recommend by author
            return self.recommend_by_author(book["authors"], num_recommendations)
        
        # Create a filter for books with matching genres
        genre_filter = None
        active_genres = []
        
        for col in self.genre_columns:
            if book[col] == 1:
                active_genres.append(col.replace("is_", ""))
                if genre_filter is None:
                    genre_filter = (self.df[col] == 1)
                else:
                    genre_filter |= (self.df[col] == 1)
        
        if genre_filter is None:
            # No genre data, recommend popular books instead
            print("No genre data available, recommending popular books")
            return self.df.sort_values(["average_rating", "ratings_count"], 
                                     ascending=[False, False]).head(num_recommendations)
        
        print(f"Book genres: {', '.join(active_genres)}")
        
        # Apply filter and exclude the source book
        recommendations = self.df[genre_filter & (self.df["book_id"] != book["book_id"])]
        
        # Calculate genre match score (how many genres in common)
        def genre_match_score(row):
            score = 0
            for col in self.genre_columns:
                if book[col] == 1 and row[col] == 1:
                    score += 1
            return score
        
        # Add match score and sort
        recommendations["genre_match"] = recommendations.apply(genre_match_score, axis=1)
        recommendations = recommendations.sort_values(["genre_match", "average_rating", "ratings_count"], 
                                                  ascending=[False, False, False])
        
        print(f"Found {len(recommendations)} books matching at least one genre")
        return recommendations.head(num_recommendations)
    
    def recommend_by_author(self, author, num_recommendations=5):
        """Recommend books by the same author."""
        if pd.isna(author) or not author:
            return pd.DataFrame()
        
        # Find other books by the same author
        recommendations = self.df[self.df["authors"].str.lower().str.contains(author.lower())]
        
        # Sort by rating and popularity
        recommendations = recommendations.sort_values(["average_rating", "ratings_count"], 
                                                  ascending=[False, False])
        
        return recommendations.head(num_recommendations)
    
    def recommend_for_user(self, liked_books, num_recommendations=10):
        """Recommend books based on a list of books a user liked."""
        if self.df is None:
            if not self.load_data():
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
        
        print(f"Found {len(user_books)} of your liked books in the database")
        
        # Collect similar book IDs from all books
        all_similar_ids = []
        for book in user_books:
            if "similar_books_list" in book and len(book["similar_books_list"]) > 0:
                all_similar_ids.extend(book["similar_books_list"])
        
        # Get recommendations based on explicitly similar books if available
        similar_recommendations = pd.DataFrame()
        if all_similar_ids:
            similar_book_counts = Counter(all_similar_ids)
            unique_similar_ids = list(similar_book_counts.keys())
            
            # Get books that are in our database
            similar_recommendations = self.df[self.df["book_id"].isin(unique_similar_ids)]
            
            # Add frequency score
            similar_recommendations["frequency"] = similar_recommendations["book_id"].apply(
                lambda x: similar_book_counts[x]
            )
            
            # Sort by frequency and rating
            similar_recommendations = similar_recommendations.sort_values(
                ["frequency", "average_rating"], ascending=[False, False]
            )
        
        # Get genre-based recommendations for each book
        genre_recommendations = []
        for book in user_books:
            book_recs = self.recommend_by_genre_match(book, num_recommendations=5)
            if len(book_recs) > 0:
                genre_recommendations.append(book_recs)
        
        # Combine all recommendations
        all_recommendations = []
        
        # Add similar book recommendations if available
        if len(similar_recommendations) > 0:
            all_recommendations.append(similar_recommendations)
        
        # Add genre-based recommendations
        if genre_recommendations:
            all_recommendations.extend(genre_recommendations)
        
        if not all_recommendations:
            print("Could not generate recommendations based on your books")
            return pd.DataFrame()
        
        # Combine all recommendations
        combined_recommendations = pd.concat(all_recommendations)
        
        # Remove books the user already likes
        user_book_ids = [book["book_id"] for book in user_books]
        combined_recommendations = combined_recommendations[~combined_recommendations["book_id"].isin(user_book_ids)]
        
        # Count frequency of recommendations and add as a score if not already present
        if "frequency" not in combined_recommendations.columns:
            book_counts = Counter(combined_recommendations["book_id"])
            combined_recommendations = combined_recommendations.drop_duplicates(subset=["book_id"])
            combined_recommendations["frequency"] = combined_recommendations["book_id"].apply(lambda x: book_counts[x])
        else:
            # Ensure we don't have duplicates
            combined_recommendations = combined_recommendations.drop_duplicates(subset=["book_id"])
        
        # Sort by frequency and rating
        result = combined_recommendations.sort_values(["frequency", "average_rating"], ascending=[False, False])
        
        return result.head(num_recommendations)
    
    def recommend_by_genre(self, genre, min_rating=3.5, num_recommendations=10):
        """Get top books in a specific genre."""
        if self.df is None:
            if not self.load_data():
                return pd.DataFrame()
        
        # Find the correct genre column name
        genre_col = None
        for col in self.genre_columns:
            # Try to match the genre name to a column
            col_genre = col.replace("is_", "")
            if col_genre.lower() == genre.lower():
                genre_col = col
                break
        
        if not genre_col:
            print(f"Genre '{genre}' not found in database")
            print(f"Available genres: {[col.replace('is_', '') for col in self.genre_columns]}")
            return pd.DataFrame()
        
        # Filter by genre and minimum rating
        recommendations = self.df[(self.df[genre_col] == 1) & 
                                 (self.df["average_rating"] >= min_rating)]
        
        if len(recommendations) == 0:
            print(f"No books found for genre '{genre}' with rating >= {min_rating}")
            return pd.DataFrame()
        
        # Sort by rating and popularity
        return recommendations.sort_values(["average_rating", "ratings_count"], 
                                          ascending=[False, False]).head(num_recommendations)
    
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
            
            if "genres" in book and not pd.isna(book["genres"]):
                print(f"   Genres: {book['genres']}")
            
            if "genre_match" in book:
                print(f"   Genre match score: {book['genre_match']}")
            
            if "frequency" in book:
                print(f"   Recommendation strength: {book['frequency']}")
                
            print()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")


# Example usage
if __name__ == "__main__":
    # Create recommender
    recommender = SimilarFirstRecommender("books.db")
    recommender.load_data()
    
    print("\n--- FIND A BOOK BY TITLE ---")
    book = recommender.find_book(title="Harry Potter")
    if book is not None:
        print(f"Found: {book['title_without_series']} by {book['authors']}")
        print(f"Rating: {book['average_rating']} ({book['ratings_count']} ratings)")
    else:
        print("Book not found")
    
    print("\n--- RECOMMENDATIONS BASED ON A BOOK ---")
    recommendations = recommender.recommend_similar_books(title="Pride and Prejudice")
    recommender.print_recommendations(recommendations)
    
    print("\n--- RECOMMENDATIONS BASED ON MULTIPLE BOOKS ---")
    liked_books = ["The Hobbit", "Dune", "Ender's Game"]
    print(f"Books you liked: {', '.join(liked_books)}")
    recommendations = recommender.recommend_for_user(liked_books)
    recommender.print_recommendations(recommendations)
    
    print("\n--- TOP BOOKS IN A GENRE ---")
    genre = "fantasy_paranormal"
    recommendations = recommender.recommend_by_genre(genre)
    print(f"Top books in {genre}:")
    recommender.print_recommendations(recommendations)
    
    # Clean up
    recommender.close()