from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback
import pandas as pd

# Import your recommender system
from recommendation_system import DescriptionOnlyRecommender

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the recommender system
print("Initializing the recommendation system...")
recommender = DescriptionOnlyRecommender("books.db")
recommender.load_data()
recommender.prepare_vector_embeddings()
print("Recommender system initialized successfully!")

@app.route('/api/recommend', methods=['GET', 'POST'])
def get_recommendations():
    """
    Get book recommendations based on input parameters
    
    Accepted parameters:
    - book_titles: String - book title(s) to get recommendations for
    - is_multiple: Integer (0 or 1) - flag indicating if multiple books are being provided
    - num: Integer - number of recommendations to return (default: 5)
    
    Returns string recommendations in a simple text format
    """
    try:
        # Check if it's a GET or POST request and get parameters accordingly
        if request.method == 'GET':
            # Get parameters from the query string
            book_titles = request.args.get('book_titles', '')
            is_multiple = request.args.get('is_multiple', type=int, default=0)
            num_recommendations = request.args.get('num', default=5, type=int)
        else:  # POST
            # Get parameters from JSON body
            data = request.get_json()
            book_titles = data.get('book_titles', '')
            is_multiple = data.get('is_multiple', 0)
            num_recommendations = data.get('num', 5)
        
        # Validate input
        if not book_titles:
            return jsonify({
                "error": "Please provide book_titles parameter"
            }), 400
        
        # Initialize variables
        recommendations = pd.DataFrame()
        source_type = "title" if is_multiple == 0 else "titles"
        source_value = book_titles
        
        # Case 1: Single book title
        if is_multiple == 0:
            recommendations = recommender.get_recommendations(
                title=book_titles,
                num_recommendations=num_recommendations
            )
        # Case 2: Multiple titles
        else:
            recommendations = recommender.recommend_from_comma_separated_titles(
                book_titles,
                num_recommendations=num_recommendations
            )
        
        # Check if we got any recommendations
        if recommendations is None or len(recommendations) == 0:
            if is_multiple == 0:
                message = f"No recommendations found for book title: {book_titles}"
            else:
                message = f"No recommendations found for titles: {book_titles}"
                
            return jsonify({"error": message}), 404
        
        # Format the recommendations as strings
        recommendation_strings = []
        for i, (_, book) in enumerate(recommendations.iterrows(), 1):
            # Just include title and rating
            rec_string = f"{book['title_without_series']} - {book['average_rating']}"
            recommendation_strings.append(rec_string)
        
        # Create a header
        if is_multiple == 0:
            # Get the book title for better output
            book = recommender.find_book(title=book_titles)
            if book is not None:
                header = f"Recommendations based on: {book['title_without_series']}"
            else:
                header = f"Recommendations based on title: {book_titles}"
        else:
            header = f"Recommendations based on multiple titles: {book_titles}"
        
        # Combine all strings
        response_text = header + "\n\n" + "\n\n".join(recommendation_strings)
        
        # Return as JSON for API compatibility
        return jsonify({
            "is_multiple": is_multiple,
            "book_titles": book_titles,
            "num_recommendations": num_recommendations,
            "recommendations_text": response_text,
            "recommendations_list": recommendation_strings
        })
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """Home page with basic API usage instructions"""
    return """
    <h1>Book Recommender System API</h1>
    <p>Use the /api/recommend endpoint with the following parameters:</p>
    <ul>
        <li><b>book_titles</b>: Book title(s) to get recommendations for</li>
        <li><b>is_multiple</b>: Integer flag (0 or 1) indicating if multiple books are provided (0 = single book, 1 = multiple books)</li>
        <li><b>num</b>: Number of recommendations to return (default: 5)</li>
    </ul>
    <h2>Examples:</h2>
    <ul>
        <li>GET /api/recommend?book_titles=Harry+Potter&is_multiple=0&num=5</li>
        <li>GET /api/recommend?book_titles=Harry+Potter,The+Hobbit&is_multiple=1&num=8</li>
    </ul>
    <p>You can also use POST with JSON body containing the same parameters.</p>
    """

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)