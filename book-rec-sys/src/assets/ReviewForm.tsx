import React, { useState } from 'react';
import { IoIosArrowBack, IoIosStar, IoIosStarOutline } from "react-icons/io";
import { MdOutlineBookmarkAdd } from "react-icons/md";

interface ReviewFormProps {
  onBackClick: () => void;
  onSubmit: (reviewData: ReviewData) => void;
}

interface ReviewData {
  bookTitle: string;
  rating: number;
  reviewText: string;
  shelves: string[];
}

const ReviewForm: React.FC<ReviewFormProps> = ({ onBackClick, onSubmit }) => {
  const [bookTitle, setBookTitle] = useState('');
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [showShelfDropdown, setShowShelfDropdown] = useState(false);
  const [selectedShelves, setSelectedShelves] = useState<Record<string, boolean>>({});

  // Available shelves - you can customize this or make it dynamic
  const shelves = [
    { id: 'favorites', label: 'Favorites' },
      { id: 'currently-reading', label: 'Currently Reading' },
      { id: 'want-to-read', label: 'Want to Read' },
      { id: 'read-again', label: 'Read Again' }
  ];

  const handleRatingClick = (selectedRating: number) => {
    setRating(selectedRating);
  };

  const toggleShelf = (shelfId: string) => {
    setSelectedShelves(prev => ({
      ...prev,
      [shelfId]: !prev[shelfId]
    }));
  };

  const handleSubmit = () => {
    const selectedShelfIds = Object.entries(selectedShelves)
      .filter(([_, isSelected]) => isSelected)
      .map(([shelfId, _]) => shelfId);

    onSubmit({
      bookTitle,
      rating,
      reviewText,
      shelves: selectedShelfIds
    });
  };

  return (
    <div className="review-form-container">
      {/* Header with back button */}
      <div className="section-header">
        <button
          onClick={onBackClick}
          className="back-button"
        >
          <IoIosArrowBack />
        </button>
        <h3>Adding a New Review</h3>
      </div>

      {/* Form content */}
      <div className="review-form">
        {/* Book Title Input */}
        <div className="form-group">
          <label htmlFor="book-title">Book Title</label>
          <input
            type="text"
            id="book-title"
            value={bookTitle}
            onChange={(e) => setBookTitle(e.target.value)}
            className="form-control"
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              border: '1px solid #ddd',
              marginTop: '8px'
            }}
          />
        </div>

        {/* Star Rating */}
        <div className="form-group" style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label>Star Rating</label>
          <div className="star-rating" style={{ display: 'flex', gap: '4px' }}>
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => handleRatingClick(star)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                {star <= rating ? (
                  <IoIosStar size={24} color="#0F9F90" />
                ) : (
                  <IoIosStarOutline size={24} color="#0F9F90" />
                )}
              </button>
            ))}
          </div>

          {/* Add to Shelf Dropdown */}
          <div className="shelf-dropdown-container" style={{ position: 'relative' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <label style={{ marginRight: '10px' }}>Add to Shelf</label>
              <button
                type="button"
                onClick={() => setShowShelfDropdown(!showShelfDropdown)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                <MdOutlineBookmarkAdd size={20} color="#0F9F90" />
                <span>Select</span>
              </button>
            </div>

            {showShelfDropdown && (
              <div
                className="shelf-dropdown"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: '0',
                  width: '200px',
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                  zIndex: 10
                }}
              >
                <div style={{ padding: '8px 12px', borderBottom: '1px solid #eee', color: '#0F9F90', fontWeight: 'bold' }}>
                  Add to Shelf
                </div>
                {shelves.map(shelf => (
                  <div
                    key={shelf.id}
                    style={{ padding: '8px 12px', borderBottom: '1px solid #eee' }}
                  >
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={!!selectedShelves[shelf.id]}
                        onChange={() => toggleShelf(shelf.id)}
                        style={{ marginRight: '8px', accentColor: '#0F9F90' }}
                      />
                      <span style={{ color: '#0F9F90' }}>{shelf.label}</span>
                    </label>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Review Text */}
        <div className="form-group" style={{ marginTop: '20px' }}>
          <label htmlFor="review-text">Enter Your Review</label>
          <textarea
            id="review-text"
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            className="form-control"
            rows={8}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              border: '1px solid #ddd',
              marginTop: '8px',
              resize: 'vertical'
            }}
          />
        </div>

        {/* Submit Button */}
        <div className="form-actions" style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
          <button
            type="button"
            onClick={handleSubmit}
            style={{
              backgroundColor: '#0F9F90',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '10px 30px',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReviewForm;