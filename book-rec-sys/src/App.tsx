import './App.css';
import Title, { Panel } from './Home';
import GenreGrid from './GenreGrid';
import { useState } from 'react';
import { IoIosArrowBack } from "react-icons/io";

const genres = [
  "Children", "Comics & Graphic", "Mystery, Thriller & Crime", "Poetry",
  "Fantasy & Paranormal", "History & Biography", "Romance", "Young Adult"
];

const shelves = [
  "Favorites", "Currently Reading", "Want to Read", "Read Again"
];

function Web() {
  const [activeView, setActiveView] = useState<'genre' | 'shelves'>('genre');

  const handleGenreClick = (genre: string) => {
    console.log("Genre selected:", genre);
  };

  const handleShelfClick = (shelf: string) => {
    console.log("Shelf selected:", shelf);
  };


  return (
    <div>
      <Title />

      <div className="two-column-container">
        <div>
        {activeView === 'genre' ? (
        <h3 className="genre-grid" style={{ fontStyle: 'italic' }}>
          Search By Genre
        </h3>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <button
            onClick={() => setActiveView('genre')}
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
        </div>
        )}

          {activeView === 'genre' ? (
            <GenreGrid genres={genres} onGenreClick={handleGenreClick} />
          ) : (
            <GenreGrid genres={shelves} onGenreClick={handleShelfClick} />
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
