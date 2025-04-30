import React, { useState, useRef, useEffect } from 'react';
import { MdOutlineBookmarkAdd, MdBookmarkAdded } from "react-icons/md";

interface BookDropdownProps {
  bookTitle: string;
}

const BookDropdown: React.FC<BookDropdownProps> = ({ bookTitle }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedShelves, setSelectedShelves] = useState<Record<string, boolean>>({
    favorites: false,
    'currently-reading': false,
    'want-to-read': false,
    'read-again': false
  });
  const [isAddedToAnyShelf, setIsAddedToAnyShelf] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Using the same shelves as defined in App.tsx for "Your Shelves" section
  const shelfOptions = [
    { id: 'favorites', label: 'Favorites' },
    { id: 'currently-reading', label: 'Currently Reading' },
    { id: 'want-to-read', label: 'Want to Read' },
    { id: 'read-again', label: 'Read Again' }
  ];

  useEffect(() => {
    // Check if added to any shelf
    const added = Object.values(selectedShelves).some(value => value);
    setIsAddedToAnyShelf(added);
  }, [selectedShelves]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleDropdown = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const toggleShelf = (shelfId: string) => {
    setSelectedShelves(prev => ({
      ...prev,
      [shelfId]: !prev[shelfId]
    }));
  };

  const handleMarkCurrent = () => {
    console.log(`Adding "${bookTitle}" to shelves:`, 
      Object.entries(selectedShelves)
        .filter(([_, isSelected]) => isSelected)
        .map(([shelfId, _]) => shelfId)
    );
    setIsOpen(false);
  };

  return (
    <div className="book-dropdown" ref={dropdownRef}>
      <button 
        onClick={toggleDropdown}
        className="bookmark-button"
        style={{
          background: 'none',
          border: '1px solid #ddd',
          borderRadius: '4px',
          color: isAddedToAnyShelf ? '#0F9F90' : '#888',
          cursor: 'pointer',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '40px',
          height: '40px'
        }}
        title="Add to shelf"
      >
        {isAddedToAnyShelf ? <MdBookmarkAdded size={24} /> : <MdOutlineBookmarkAdd size={24} />}
      </button>

      {isOpen && (
        <div 
          className="dropdown-menu" 
          style={{
            position: 'absolute',
            right: '-10px',
            top: '45px',
            width: '220px',
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
            zIndex: 100,
            overflow: 'hidden'
          }}
        >
          <div 
            className="dropdown-header" 
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid #eee',
              color: '#0F9F90',
              fontWeight: 'bold'
            }}
          >
            Add to Shelf
          </div>
          
          <div className="dropdown-options" style={{ padding: '8px 0' }}>
            {shelfOptions.map(option => (
              <div 
                key={option.id}
                className="dropdown-option"
                style={{ 
                  padding: '8px 16px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <label 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    width: '100%',
                    cursor: 'pointer'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedShelves[option.id]}
                    onChange={() => toggleShelf(option.id)}
                    style={{ 
                      marginRight: '12px',
                      cursor: 'pointer',
                      accentColor: '#0F9F90' 
                    }}
                  />
                  <span style={{ color: '#0F9F90' }}>{option.label}</span>
                </label>
              </div>
            ))}
          </div>
          
          <div 
            className="dropdown-footer"
            style={{
              padding: '12px 16px',
              borderTop: '1px solid #eee',
              display: 'flex',
              justifyContent: 'center'
            }}
          >
          </div>
        </div>
      )}
    </div>
  );
};

export default BookDropdown;