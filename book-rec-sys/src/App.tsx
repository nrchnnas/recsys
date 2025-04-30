import './App.css';
import Title, { Panel } from './Home';
import GenreGrid from './assets/GenreGrid';
import BookList from './assets/BookList';
import ShelfDetail from './assets/ShelfDetail';
import ReviewForm from './assets/ReviewForm'; // Import the new ReviewForm component
import { useState } from 'react';
import { IoIosArrowBack } from "react-icons/io";

const genres = [
  "Children", "Comics & Graphic", "Mystery, Thriller & Crime", "Poetry",
  "Fantasy & Paranormal", "History & Biography", "Romance", "Young Adult"
];

const shelves = [
  "Favorites", "Currently Reading", "Want to Read", "Read Again"
];

// Sample data for books in shelves
const shelfBooks = {
  "Favorites": [
    { id: '1', title: "Harry Potter and the Prisoner of Azkaban" },
    { id: '2', title: "Pride and Prejudice" },
    { id: '3', title: "The Hunger Games" }
  ],
  "Currently Reading": [
    { id: '4', title: "Lord of the Rings: The Fellowship of the Ring" },
    { id: '5', title: "Dune" }
  ],
  "Want to Read": [
    { id: '6', title: "Good Omens" },
    { id: '7', title: "The Shining" },
    { id: '8', title: "The Hobbit" }
  ],
  "Read Again": [
    { id: '9', title: "To Kill a Mockingbird" },
    { id: '10', title: "1984" }
  ]
};

// Sample recommendations based on shelf
const recommendations = {
  "Favorites": [
    { id: 'r1', title: "Fantastic Beasts and Where to Find Them" },
    { id: 'r2', title: "Emma" },
    { id: 'r3', title: "Sunrise on the Reaping" }
  ],
  "Currently Reading": [
    { id: 'r4', title: "The Two Towers" },
    { id: 'r5', title: "Dune Messiah" },
    { id: 'r6', title: "Foundation" }
  ],
  "Want to Read": [
    { id: 'r7', title: "American Gods" },
    { id: 'r8', title: "Doctor Sleep" },
    { id: 'r9', title: "The Silmarillion" }
  ],
  "Read Again": [
    { id: 'r10', title: "Go Set a Watchman" },
    { id: 'r11', title: "Animal Farm" },
    { id: 'r12', title: "Brave New World" }
  ]
};

const genreBooks = {
  "Fantasy & Paranormal": [
    { title: "The Heroes of Olympus: The Lost Hero" },
    { title: "Trials of Apollo: The Hidden Oracle" },
    { title: "The Song of Achilles" },
    { title: "Tales from Ovid" },
    { title: "The Odyssey (Emily Wilson Translation)" },
    { title: "The Heroes of Olympus: Blood of Olympus" }
  ],
  "Children": [
    { title: "Harry Potter and the Sorcerer's Stone" },
    { title: "Charlotte's Web" }
  ],
  "Comics & Graphic": [
    { title: "Maus" },
    { title: "Watchmen" }
  ],
  "Mystery, Thriller & Crime": [
    { title: "Gone Girl" },
    { title: "The Girl with the Dragon Tattoo" }
  ],
  "Poetry": [
    { title: "Milk and Honey" },
    { title: "Where the Sidewalk Ends" }
  ],
  "History & Biography": [
    { title: "Sapiens" },
    { title: "The Diary of a Young Girl" }
  ],
  "Romance": [
    { title: "Pride and Prejudice" },
    { title: "Outlander" }
  ],
  "Young Adult": [
    { title: "The Hunger Games" },
    { title: "The Fault in Our Stars" }
  ]
};

function Web() {
  // Add 'new-review' to the possible view states
  const [activeView, setActiveView] = useState<'genre' | 'shelves' | 'book-list' | 'shelf-detail' | 'new-review'>('genre');
  const [selectedGenre, setSelectedGenre] = useState<string>('');
  const [selectedShelf, setSelectedShelf] = useState<string>('');

  const handleGenreClick = (genre: string) => {
    setSelectedGenre(genre);
    setActiveView('book-list');
  };

  const handleShelfClick = (shelf: string) => {
    console.log("Shelf selected:", shelf);
    setSelectedShelf(shelf);
    setActiveView('shelf-detail');
  };

  const handleBackToGenre = () => {
    setActiveView('genre');
  };

  const handleBackToShelves = () => {
    setActiveView('shelves');
  };

  // Handler for submitting a new review
  const handleReviewSubmit = (reviewData: any) => {
    console.log("Review submitted:", reviewData);
    // Here you would typically store the review data
    // For now, just go back to the genre view
    setActiveView('genre');
  };

  return (
    <div>
      <Title />

      <div className="two-column-container">
        <div>
          {activeView === 'genre' && (
            <>
              <div className="section-header">
                <h3>Search By Genre</h3>
              </div>
              <GenreGrid genres={genres} onGenreClick={handleGenreClick} />
            </>
          )}

          {activeView === 'shelves' && (
            <>
              <div className="section-header">
                <button
                  onClick={handleBackToGenre}
                  className="back-button"
                >
                  <IoIosArrowBack />
                </button>
                <h3>Your Shelves</h3>
              </div>
              <GenreGrid genres={shelves} onGenreClick={handleShelfClick} />
            </>
          )}

          {activeView === 'book-list' && (
            <BookList 
              title={selectedGenre}
              books={genreBooks[selectedGenre as keyof typeof genreBooks] || []} 
              onBackClick={handleBackToGenre} 
            />
          )}
          
          {activeView === 'shelf-detail' && (
            <ShelfDetail
              shelfName={selectedShelf}
              books={shelfBooks[selectedShelf as keyof typeof shelfBooks] || []}
              recommendedBooks={recommendations[selectedShelf as keyof typeof recommendations] || []}
              onBackClick={handleBackToShelves}
            />
          )}

          {/* New Review Form */}
          {activeView === 'new-review' && (
            <ReviewForm 
              onBackClick={handleBackToGenre}
              onSubmit={handleReviewSubmit}
            />
          )}
        </div>

        <div>
          <Panel 
            onViewShelvesClick={() => setActiveView('shelves')} 
            onAddNewReviewClick={() => setActiveView('new-review')} // Add handler for the review button
          />
        </div>
      </div>
    </div>
  );
}

export default Web;