import './App.css';
import Title, { Panel } from './Home';
import GenreGrid from './GenreGrid';
import BookList from './BookList';
import { useState } from 'react';
import { IoIosArrowBack } from "react-icons/io";

const genres = [
  "Children", "Comics & Graphic", "Mystery, Thriller & Crime", "Poetry",
  "Fantasy & Paranormal", "History & Biography", "Romance", "Young Adult"
];

const shelves = [
  "Favorites", "Currently Reading", "Want to Read", "Read Again"
];

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
  const [activeView, setActiveView] = useState<'genre' | 'shelves' | 'book-list'>('genre');
  const [selectedGenre, setSelectedGenre] = useState<string>('');

  const handleGenreClick = (genre: string) => {
    setSelectedGenre(genre);
    setActiveView('book-list');
  };

  const handleShelfClick = (shelf: string) => {
    console.log("Shelf selected:", shelf);
    setActiveView('shelves');
  };

  const handleBackToGenre = () => {
    setActiveView('genre');
  };

  return (
    <div>
      <Title />

      <div className="two-column-container">
        <div>
          {activeView === 'genre' && (
            <>
              <h3 className="genre-grid" style={{ fontStyle: 'italic' }}>
                Search By Genre
              </h3>
              <GenreGrid genres={genres} onGenreClick={handleGenreClick} />
            </>
          )}

          {activeView === 'shelves' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <button
                onClick={handleBackToGenre}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#0F9F90',
                  cursor: 'pointer',
                  padding: 0,
                  fontSize: '1.5rem',
                }}
                className="genre-grid-icon"
              >
                <IoIosArrowBack />
              </button>
              <h3 className="genre-grid">Your Shelves</h3>
              <GenreGrid genres={shelves} onGenreClick={handleShelfClick} />
            </div>
          )}

          {activeView === 'book-list' && (
            <BookList 
              title={selectedGenre}
              books={genreBooks[selectedGenre as keyof typeof genreBooks] || []} 
              onBackClick={handleBackToGenre} 
            />
          )}
        </div>

        <div>
          <Panel onViewShelvesClick={() => setActiveView('shelves')} />
        </div>
      </div>
    </div>
  );
}

export default Web;