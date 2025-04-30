import { IoIosArrowBack } from "react-icons/io";
import BookDropdown from './BookDropdown'; // Import the BookDropdown component

interface Book {
  id: string;
  title: string;
  isBookmarked?: boolean;
}

interface ShelfDetailProps {
  shelfName: string;
  books: Book[];
  recommendedBooks: Book[];
  onBackClick: () => void;
}

const ShelfDetail: React.FC<ShelfDetailProps> = ({
  shelfName,
  books,
  recommendedBooks,
  onBackClick
}) => {
  return (
    <div>
      {/* Header with back button and shelf name - properly aligned with section-header class */}
      <div className="section-header">
        <button
          onClick={onBackClick}
          className="back-button"
        >
          <IoIosArrowBack />
        </button>
        <h3>{shelfName}</h3>
      </div>

      {/* Books in this shelf - properly aligned */}
      <div className="genre-grid" style={{ gridTemplateColumns: '1fr', maxWidth: '100%' }}>
        {books.map(book => (
          <div 
            key={book.id} 
            className="book-item"
          >
            <span style={{ fontWeight: '500' }}>{book.title}</span>
            <div className="book-actions" style={{ display: 'flex', gap: '8px' }}>
              <button 
                className="icon-button"
              >
              </button>
              <BookDropdown bookTitle={book.title} />
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations section - using section-header for consistency */}
      <div className="section-header" style={{ marginTop: '20px' }}>
        <h3>Based on your shelf, we think you'll also like...</h3>
      </div>
      
      {/* Recommended books - properly aligned */}
      <div className="genre-grid" style={{ gridTemplateColumns: '1fr', maxWidth: '100%' }}>
        {recommendedBooks.map(book => (
          <div 
            key={book.id}
            className="recommended-book-item"
          >
            <span style={{ fontWeight: '500' }}>{book.title}</span>
            <BookDropdown bookTitle={book.title} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default ShelfDetail;