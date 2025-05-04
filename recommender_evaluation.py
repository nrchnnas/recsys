import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from collections import Counter
import sys
import os
import traceback
import io

# Import the DescriptionOnlyRecommender class directly
from recommendation_system import DescriptionOnlyRecommender

# Windows-compatible encoding fixes
try:
    # Handle Windows console encoding
    if sys.platform == 'win32':
        # Try to set console code page to UTF-8
        os.system('chcp 65001 > NUL')
        
        # Check if running in a standard Windows console
        if hasattr(sys.stdout, 'reconfigure'):
            # For Python 3.7+ 
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        else:
            # For older Python versions, try using specialized handling
            try:
                import win_unicode_console
                win_unicode_console.enable()
            except ImportError:
                # If win_unicode_console is not available, just try to use a reasonable fallback
                pass
    else:
        # Non-Windows systems
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception as e:
    print(f"Warning: Could not configure console encoding: {e}")
    print("Special characters may not display correctly.")

class RecommenderEvaluator:
    """
    Evaluation class for the Book Recommender System that calculates:
    - NDCG (Normalized Discounted Cumulative Gain)
    - Novelty
    - Precision@k
    """
    
    def __init__(self, recommender, interactions_path, k=5):
        """
        Initialize the evaluator.
        
        Args:
            recommender: The recommendation system instance
            interactions_path: Path to the user interactions CSV file
            k: Number of recommendations to evaluate (default: 5)
        """
        self.recommender = recommender
        self.interactions_df = pd.read_csv(interactions_path)
        self.k = k
        
        # Make sure the recommender has data loaded
        if self.recommender.df is None:
            self.recommender.load_data()
            self.recommender.prepare_vector_embeddings()
        
        # Calculate book popularity for novelty metric
        self.calculate_book_popularity()
        
    def calculate_book_popularity(self):
        """Calculate popularity of each book (percentage of users who have read it)"""
        # Count unique users who have read each book
        book_reader_counts = self.interactions_df.groupby('book_id').user_id.nunique()
        
        # Total number of unique users
        total_users = self.interactions_df.user_id.nunique()
        
        # Calculate popularity as percentage of users who read each book
        self.popularity_scores = book_reader_counts / total_users
    
    def print_debug_info(self):
        """Print debug information about the data."""
        try:
            print("\n=== DEBUG INFORMATION ===")
            
            # Check for book ID overlap between interaction data and recommender data
            interaction_book_ids = set(self.interactions_df['book_id'].unique())
            recommender_book_ids = set(self.recommender.df['book_id'].unique())
            
            overlap = interaction_book_ids.intersection(recommender_book_ids)
            
            print(f"Interaction data has {len(interaction_book_ids)} unique book IDs")
            print(f"Recommender data has {len(recommender_book_ids)} unique book IDs")
            print(f"Overlap: {len(overlap)} book IDs")
            print(f"Overlap percentage: {len(overlap) / len(interaction_book_ids) * 100:.2f}%")
            
            # Check for user interaction counts
            user_interaction_counts = self.interactions_df.groupby('user_id').size()
            print(f"User interaction count statistics:")
            print(f"  Min: {user_interaction_counts.min()}")
            print(f"  Max: {user_interaction_counts.max()}")
            print(f"  Mean: {user_interaction_counts.mean():.2f}")
            print(f"  Median: {user_interaction_counts.median()}")
            
            # Count users with sufficient interactions (3+)
            users_with_sufficient = (user_interaction_counts >= 3).sum()
            print(f"Users with 3+ interactions: {users_with_sufficient} ({users_with_sufficient / len(user_interaction_counts) * 100:.2f}%)")
            
            # Check rating distribution
            print(f"Rating distribution:")
            print(self.interactions_df['rating'].value_counts().sort_index())
            
            # Check for high ratings (4+)
            high_ratings = (self.interactions_df['rating'] >= 4).sum()
            print(f"Interactions with ratings 4+: {high_ratings} ({high_ratings / len(self.interactions_df) * 100:.2f}%)")
            
            # Count users with at least one high rating
            users_with_high_ratings = self.interactions_df[self.interactions_df['rating'] >= 4]['user_id'].nunique()
            print(f"Users with at least one 4+ rating: {users_with_high_ratings} ({users_with_high_ratings / self.interactions_df['user_id'].nunique() * 100:.2f}%)")
            
            # Check format of book IDs in both dataframes
            print(f"Book ID type in interactions: {type(self.interactions_df['book_id'].iloc[0]).__name__}")
            print(f"Book ID type in recommender: {type(self.recommender.df['book_id'].iloc[0]).__name__}")
            
            # Show some sample book IDs from both datasets
            print(f"Sample interaction book IDs: {list(self.interactions_df['book_id'].head(3))}")
            print(f"Sample recommender book IDs: {list(self.recommender.df['book_id'].head(3))}")
            
            print("=== END DEBUG INFO ===\n")
        except Exception as e:
            print(f"Error printing debug info: {e}")
            traceback.print_exc()
        
    def prepare_user_data(self, user_id, test_size=0.2, min_interactions=3):
        """
        Prepare training and testing data for a specific user.
        
        Args:
            user_id: User ID to evaluate
            test_size: Proportion of interactions to use for testing
            min_interactions: Minimum number of interactions needed
            
        Returns:
            train_df, test_df if successful, otherwise None, None
        """
        # Get all interactions for this user
        user_interactions = self.interactions_df[self.interactions_df['user_id'] == user_id]
        
        # Check if user has minimum required interactions
        if len(user_interactions) < min_interactions:
            print(f"User {user_id} has fewer than {min_interactions} interactions.")
            return None, None
        
        # Make sure all book IDs are in our recommender's database
        valid_interactions = user_interactions[user_interactions['book_id'].isin(self.recommender.df['book_id'])]
        
        if len(valid_interactions) < min_interactions:
            print(f"User {user_id} has fewer than {min_interactions} valid book interactions.")
            return None, None
        
        # Check for high ratings to ensure we have relevant items
        if len(valid_interactions[valid_interactions['rating'] >= 4]) == 0:
            print(f"User {user_id} has no highly-rated books (rating >= 4).")
            return None, None
            
        # Split into train and test sets
        try:
            train_df, test_df = train_test_split(valid_interactions, test_size=test_size, random_state=42)
            return train_df, test_df
        except Exception as e:
            print(f"Error splitting data for user {user_id}: {e}")
            return None, None
    
    def generate_recommendations_for_user(self, user_id, train_df):
        """
        Generate recommendations for a user based on their training data.
        
        Args:
            user_id: User ID
            train_df: DataFrame with user's training interactions
            
        Returns:
            DataFrame with recommendations
        """
        # Extract book IDs from training data
        training_book_ids = train_df['book_id'].tolist()
        
        # Find the actual book objects in the recommender
        training_books = []
        for book_id in training_book_ids:
            book = self.recommender.find_book(book_id=book_id)
            if book is not None:
                training_books.append(book)
        
        if not training_books:
            print(f"No training books found for user {user_id} in recommender database.")
            return pd.DataFrame()
        
        # Get recommendations based on training books
        all_recommendations = []
        
        print(f"Generating recommendations for user {user_id} based on {len(training_books)} books...")
        for book in training_books:
            # Temporarily redirect stdout to suppress verbose output from get_recommendations
            original_stdout = sys.stdout
            
            # Windows-compatible output redirection
            try:
                # Try using a Python file object (works on most systems)
                null_file = open(os.devnull, 'w', encoding='utf-8', errors='ignore')
                sys.stdout = null_file
            except:
                # Fallback: just create a dummy stream that discards output
                class NullWriter:
                    def write(self, text): pass
                    def flush(self): pass
                    def close(self): pass
                sys.stdout = NullWriter()
            
            try:
                book_recs = self.recommender.get_recommendations(
                    book_id=book['book_id'], 
                    num_recommendations=self.k
                )
                
                if len(book_recs) > 0:
                    all_recommendations.append(book_recs)
            except Exception as e:
                # Restore stdout before printing errors
                sys.stdout = original_stdout
                
                # Print error with safe encoding handling
                try:
                    print(f"Error getting recommendations for book {book['book_id']}: {e}")
                except UnicodeEncodeError:
                    # Fallback for encoding errors
                    print(f"Error getting recommendations for book {book['book_id']}: <encoding error>")
                    print(f"Error type: {type(e).__name__}")
                continue
            finally:
                # Restore stdout and close file if it was opened
                sys.stdout = original_stdout
                if 'null_file' in locals() and null_file:
                    try:
                        null_file.close()
                    except:
                        pass
        
        if not all_recommendations:
            print(f"No recommendations generated for user {user_id}.")
            return pd.DataFrame()
        
        # Combine recommendations
        combined_recommendations = pd.concat(all_recommendations)
        
        # Remove books that were in the training set
        combined_recommendations = combined_recommendations[
            ~combined_recommendations['book_id'].isin(training_book_ids)
        ]
        
        if len(combined_recommendations) == 0:
            print(f"No recommendations left after removing training books for user {user_id}.")
            return pd.DataFrame()
        
        # Remove duplicates and count frequency
        combined_recommendations = combined_recommendations.drop_duplicates(subset=['book_id'])
        book_counts = Counter(combined_recommendations['book_id'])
        combined_recommendations['frequency'] = combined_recommendations['book_id'].apply(lambda x: book_counts[x])
        
        # Sort by frequency and score
        sorted_recommendations = combined_recommendations.sort_values(
            ['frequency', 'final_score'], 
            ascending=[False, False]
        )
        
        return sorted_recommendations.head(self.k)
    
    def calculate_ndcg(self, recommendations, test_df, k=None):
        """
        Calculate NDCG (Normalized Discounted Cumulative Gain) for recommendations.
        
        Args:
            recommendations: DataFrame with recommendations
            test_df: DataFrame with test interactions
            k: Number of recommendations to consider (default: None, uses self.k)
            
        Returns:
            NDCG score
        """
        if k is None:
            k = self.k
            
        if len(recommendations) == 0 or len(test_df) == 0:
            return 0.0
        
        # Limit to top-k recommendations
        recommendations = recommendations.head(k)
        
        # Create relevance scores based on test ratings
        relevance = []
        for _, rec in recommendations.iterrows():
            book_id = rec['book_id']
            # Find if this book is in the test set
            matches = test_df[test_df['book_id'] == book_id]
            if len(matches) > 0:
                # Use rating as relevance score (normalized to 0-1 scale)
                rating = matches.iloc[0]['rating']
                relevance.append(rating / 5.0)  # Assuming 5-star scale
            else:
                relevance.append(0.0)
        
        # Calculate DCG
        dcg = 0.0
        for i, rel in enumerate(relevance):
            # i+1 because position is 1-indexed in the formula
            dcg += rel / np.log2(i + 2)  # +2 because log_2(1) = 0
        
        # Calculate ideal DCG: sort relevance scores in descending order
        ideal_relevance = sorted(relevance, reverse=True)
        idcg = 0.0
        for i, rel in enumerate(ideal_relevance):
            idcg += rel / np.log2(i + 2)
        
        # Return NDCG (handle division by zero)
        if idcg > 0:
            return dcg / idcg
        return 0.0
    
    def calculate_novelty(self, recommendations, k=None):
        """
        Calculate novelty of recommendations based on inverse popularity.
        
        Args:
            recommendations: DataFrame with recommendations
            k: Number of recommendations to consider
            
        Returns:
            Average novelty score
        """
        if k is None:
            k = self.k
            
        if len(recommendations) == 0:
            return 0.0
        
        # Limit to top-k recommendations
        recommendations = recommendations.head(k)
        
        # Calculate novelty as 1 - popularity
        novelty_scores = []
        for _, rec in recommendations.iterrows():
            book_id = rec['book_id']
            popularity = self.popularity_scores.get(book_id, 0)
            novelty = 1 - popularity
            novelty_scores.append(novelty)
        
        # Return average novelty
        if novelty_scores:
            return np.mean(novelty_scores)
        return 0.0
    
    def calculate_precision_at_k(self, recommendations, test_df, k=None, relevance_threshold=3.5):
        """
        Calculate Precision@k: what fraction of recommendations were relevant.
        
        Args:
            recommendations: DataFrame with recommendations
            test_df: DataFrame with test interactions
            k: Number of recommendations to consider
            relevance_threshold: Minimum rating to consider relevant
            
        Returns:
            Precision@k score
        """
        if k is None:
            k = self.k
            
        if len(recommendations) == 0 or len(test_df) == 0:
            return 0.0
        
        # Limit to top-k recommendations
        recommendations = recommendations.head(k)
        actual_k = len(recommendations)  # In case there are fewer than k recommendations
        
        # Find relevant books in test set
        relevant_books = set(test_df[test_df['rating'] >= relevance_threshold]['book_id'])
        
        # Count how many recommended books were relevant
        recommended_book_ids = set(recommendations['book_id'])
        relevant_recommendations = recommended_book_ids.intersection(relevant_books)
        
        # Calculate precision
        if actual_k > 0:
            return len(relevant_recommendations) / actual_k
        return 0.0
    
    def calculate_recall(self, recommendations, test_df, relevance_threshold=3.5):
        """
        Calculate Recall: what fraction of relevant items were recommended.
        
        Args:
            recommendations: DataFrame with recommendations
            test_df: DataFrame with test interactions
            relevance_threshold: Minimum rating to consider relevant
            
        Returns:
            Recall score
        """
        if len(recommendations) == 0 or len(test_df) == 0:
            return 0.0
        
        # Find relevant books in test set
        relevant_books = set(test_df[test_df['rating'] >= relevance_threshold]['book_id'])
        
        if len(relevant_books) == 0:
            return 0.0
        
        # Count how many recommended books were relevant
        recommended_book_ids = set(recommendations['book_id'])
        relevant_recommendations = recommended_book_ids.intersection(relevant_books)
        
        # Calculate recall
        return len(relevant_recommendations) / len(relevant_books)
    
    def evaluate_for_user(self, user_id):
        """
        Evaluate recommender performance for a single user.
        
        Args:
            user_id: User ID to evaluate
            
        Returns:
            Dictionary with evaluation metrics or None if evaluation not possible
        """
        # Prepare user data
        train_df, test_df = self.prepare_user_data(user_id)
        if train_df is None or len(train_df) == 0 or len(test_df) == 0:
            return None
        
        # Generate recommendations
        recommendations = self.generate_recommendations_for_user(user_id, train_df)
        if len(recommendations) == 0:
            return None
        
        # Calculate metrics
        ndcg = self.calculate_ndcg(recommendations, test_df)
        novelty = self.calculate_novelty(recommendations)
        precision = self.calculate_precision_at_k(recommendations, test_df)
        recall = self.calculate_recall(recommendations, test_df)
        
        return {
            'user_id': user_id,
            'ndcg': ndcg,
            'novelty': novelty,
            'precision': precision,
            'recall': recall,
            'num_recommendations': len(recommendations),
            'num_train_items': len(train_df),
            'num_test_items': len(test_df)
        }
    
    def evaluate_all_users(self, max_users=None, debug=False, min_interactions=1):
        """
        Evaluate the recommender system for all users.
        
        Args:
            max_users: Maximum number of users to evaluate (for testing)
            debug: Whether to print debug information
            min_interactions: Minimum number of interactions required (default: 1)
            
        Returns:
            DataFrame with evaluation results for all users, and dictionary with average metrics
        """
        if debug:
            self.print_debug_info()
        
        # Get unique user IDs
        user_ids = self.interactions_df['user_id'].unique()
        if max_users is not None:
            user_ids = user_ids[:max_users]
        
        print(f"Evaluating {len(user_ids)} users...")
        
        # Evaluate each user
        results = []
        successful_evaluations = 0
        for i, user_id in enumerate(user_ids):
            if i % 10 == 0 or i == len(user_ids) - 1:
                print(f"Processing user {i+1}/{len(user_ids)} - {successful_evaluations} successful evaluations so far")
                
            try:
                # Modify the prepare_user_data call to use the custom min_interactions parameter
                train_df, test_df = self.prepare_user_data(user_id, min_interactions=min_interactions)
                if train_df is None or len(train_df) == 0 or len(test_df) == 0:
                    continue
                    
                # Generate recommendations
                recommendations = self.generate_recommendations_for_user(user_id, train_df)
                if len(recommendations) == 0:
                    continue
                    
                # Calculate metrics
                try:
                    ndcg = self.calculate_ndcg(recommendations, test_df)
                except Exception as e:
                    print(f"Error calculating NDCG for user {user_id}: {e}")
                    ndcg = 0.0
                    
                try:
                    novelty = self.calculate_novelty(recommendations)
                except Exception as e:
                    print(f"Error calculating novelty for user {user_id}: {e}")
                    novelty = 0.0
                    
                try:
                    precision = self.calculate_precision_at_k(recommendations, test_df)
                except Exception as e:
                    print(f"Error calculating precision for user {user_id}: {e}")
                    precision = 0.0
                    
                try:
                    recall = self.calculate_recall(recommendations, test_df)
                except Exception as e:
                    print(f"Error calculating recall for user {user_id}: {e}")
                    recall = 0.0
                
                # Add user result
                results.append({
                    'user_id': user_id,
                    'ndcg': ndcg,
                    'novelty': novelty,
                    'precision': precision,
                    'recall': recall,
                    'num_recommendations': len(recommendations),
                    'num_train_items': len(train_df),
                    'num_test_items': len(test_df)
                })
                successful_evaluations += 1
            except Exception as e:
                print(f"Error evaluating user {user_id}: {e}")
        
        # Create empty dataframe with required columns if no successful evaluations
        if not results:
            print("\nWARNING: No successful evaluations completed!")
            print("Creating empty results with default columns...")
            
            empty_results = pd.DataFrame({
                'user_id': [],
                'ndcg': [],
                'novelty': [],
                'precision': [],
                'recall': [],
                'num_recommendations': [],
                'num_train_items': [],
                'num_test_items': []
            })
            
            empty_metrics = {
                'avg_ndcg': 0.0,
                'avg_novelty': 0.0,
                'avg_precision': 0.0,
                'avg_recall': 0.0,
                'successful_evaluations': 0,
                'total_users': len(user_ids)
            }
            
            return empty_results, empty_metrics
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculate average metrics
        avg_metrics = {
            'avg_ndcg': results_df['ndcg'].mean() if 'ndcg' in results_df.columns else 0.0,
            'avg_novelty': results_df['novelty'].mean() if 'novelty' in results_df.columns else 0.0,
            'avg_precision': results_df['precision'].mean() if 'precision' in results_df.columns else 0.0,
            'avg_recall': results_df['recall'].mean() if 'recall' in results_df.columns else 0.0,
            'successful_evaluations': len(results_df),
            'total_users': len(user_ids)
        }
        
        print("\nEvaluation Results:")
        print(f"Evaluated {len(results_df)} out of {len(user_ids)} users successfully ({len(results_df)/len(user_ids)*100:.1f}%)")
        print(f"Average NDCG: {avg_metrics['avg_ndcg']:.4f}")
        print(f"Average Novelty: {avg_metrics['avg_novelty']:.4f}")
        print(f"Average Precision@{self.k}: {avg_metrics['avg_precision']:.4f}")
        print(f"Average Recall: {avg_metrics['avg_recall']:.4f}")
        
        return results_df, avg_metrics


# Example usage
if __name__ == "__main__":
    try:
        # Initialize the recommender
        print("Initializing recommendation system...")
        recommender = DescriptionOnlyRecommender("books.db")
        recommender.load_data()
        recommender.prepare_vector_embeddings()
        
        # Check if interaction file exists
        interactions_file = input("Enter the path to the user interactions CSV file: ").strip()
        print(f"Using interaction data from: {interactions_file}")
        
        # Initialize the evaluator
        evaluator = RecommenderEvaluator(
            recommender=recommender,
            interactions_path=interactions_file,
            k=5  # Evaluate top 5 recommendations
        )
        
        # Ask if user wants to see debug info
        print("\nWould you like to see detailed debug information about your data?")
        debug_choice = input("Enter 'y' for yes, anything else for no: ").lower().strip() == 'y'
        
        # Ask if user wants to evaluate all users or a sample
        print("\nHow many users would you like to evaluate?")
        print("1. All users (may take a long time)")
        print("2. Sample of users (faster for testing)")
        choice = input("Enter your choice (1 or 2): ")
        
        max_users = None
        if choice == "2":
            sample_size = input("Enter sample size (e.g., 100): ")
            try:
                max_users = int(sample_size)
            except ValueError:
                print("Invalid input, using 100 as default")
                max_users = 100
        
        # Ask about minimum interactions threshold
        print("\nWhat should be the minimum number of interactions required for evaluation?")
        print("1. Default (3 interactions)")
        print("2. Lower threshold (1 interaction - will include more users)")
        min_choice = input("Enter your choice (1 or 2): ")
        
        min_interactions = 3  # Default
        if min_choice == "2":
            min_interactions = 1
        
        # Evaluate users
        results_df, avg_metrics = evaluator.evaluate_all_users(
            max_users=max_users, 
            debug=debug_choice,
            min_interactions=min_interactions
        )
        
        # Save results to CSV
        if len(results_df) > 0:
            results_file = "evaluation_results.csv"
            results_df.to_csv(results_file, index=False)
            print(f"\nDetailed results saved to: {results_file}")
        else:
            print("\nNo results to save to CSV.")
        
        # Save average metrics
        summary_file = "evaluation_summary.csv"
        pd.DataFrame([avg_metrics]).to_csv(summary_file, index=False)
        print(f"Summary metrics saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        traceback.print_exc()