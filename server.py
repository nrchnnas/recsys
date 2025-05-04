from flask import Flask, request, jsonify
from flask_cors import CORS
import os

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

    try:
        # Check if it's a GET or POST request and get parameters accordingly
        if request.method == 'GET':
            # Get parameters from the query string
            book_title = request.args.get('book_title', '')
            num_recommendations = request.args.get('num', default=5, type=int)
        else:  # POST
            # Get parameters from JSON body
            data = request.get_json()
            book_title = data.get('book_title', '')
            num_recommendations = data.get('num', 5)
        
        # Validate input
        if not book_title:
            return jsonify({
                "error": "Please provide book_title parameter"
            }), 400
        
        # Get recommendations for the single book title
        recommendations = recommender.get_recommendations(
            title=book_title,
            num_recommendations=num_recommendations
        )
        
        # Check if we got any recommendations
        if recommendations is None or len(recommendations) == 0:
            message = f"No recommendations found for book title: {book_title}"
            return jsonify({"error": message}), 404
        
        # Format the recommendations as strings
        recommendation_strings = []
        for i, (_, book) in enumerate(recommendations.iterrows(), 1):
            # Just include title and rating
            rec_string = f"{book['title_without_series']}"
            recommendation_strings.append(rec_string)
        
        # Create a header
        # Get the book title for better output
        book = recommender.find_book(title=book_title)
        if book is not None:
            header = f"Recommendations based on: {book['title_without_series']}"
        else:
            header = f"Recommendations based on title: {book_title}"
        
        # Combine all strings
        response_text = header + "\n\n" + "\n\n".join(recommendation_strings)
        
        # Return as JSON for API compatibility
        return jsonify({
            "book_title": book_title,
            "num_recommendations": num_recommendations,
            "recommendations_text": response_text,
            "recommendations_list": recommendation_strings
        })
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """Home page with basic API usage instructions"""
    return """
    <h1>Book Recommender System API</h1>
    <p>Use the /api/recommend endpoint with the following parameters:</p>
    <ul>
        <li><b>book_title</b>: Book title to get recommendations for</li>
        <li><b>num</b>: Number of recommendations to return (default: 5)</li>
    </ul>
    <h2>Examples:</h2>
    <ul>
        <li>GET /api/recommend?book_title=Harry+Potter&num=5</li>
    </ul>
    <p>You can also use POST with JSON body containing the same parameters.</p>
    """

if __name__ == '__main__':
    # Get port from environment variable
    port = int(os.environ.get('PORT', 8000))
    
    # Run the Flask app
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)