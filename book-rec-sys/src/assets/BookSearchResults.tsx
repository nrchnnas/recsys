import { useState, useEffect } from 'react';
import { IoIosArrowBack } from "react-icons/io";

interface Book {
  title: string;
}

interface BookSearchResultsProps {
  query: string;
  onBackClick: () => void;
}

const BookSearchResults = ({ query, onBackClick }: BookSearchResultsProps) => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBooks = async () => {
      if (!query) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Call the API endpoint
        const response = await fetch(`/api/recommend?book_title=${encodeURIComponent(query)}&num=10`);
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Transform the recommendations_list into the format we expect
        if (data.recommendations_list && Array.isArray(data.recommendations_list)) {
          const formattedBooks = data.recommendations_list.map((rec: string) => ({
            title: rec
          }));
          setBooks(formattedBooks);
        } else {
          // Fallback - if we didn't get results in the expected format
          setBooks([]);
          setError('No results found');
        }
      } catch (err) {
        console.error('Error fetching book recommendations:', err);
        setError('Failed to fetch recommendations. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  }, [query]);

  return (
    <div>
      <div className="section-header">
        <button onClick={onBackClick} className="back-button">
          <IoIosArrowBack />
        </button>
        <h3>Results for "{query}"</h3>
      </div>

      <div className="book-list" style={{ position: 'relative', top: '112px', left: '100px', maxWidth: '600px' }}>
        {loading && <p>Loading...</p>}
        
        {error && <p className="error-message">{error}</p>}
        
        {!loading && !error && books.length === 0 && (
          <p>No books found for "{query}". Try another search term.</p>
        )}
        
        {!loading && !error && books.length > 0 && (
          <div>
            {books.map((book, index) => (
              <div key={index} className="book-item">
                <span>{book.title}</span>
                <div className="book-actions">
                  {/* Book actions can be added here */}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BookSearchResults;