import './App.css';
import Title, { Panel } from './Home';
import GenreGrid from './GenreGrid';
import { useState } from 'react';

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
          <h3 className="genre-grid" style={{ fontStyle: 'italic' }}>
            {activeView === 'genre' ? 'Search By Genre' : 'Your Shelves'}
          </h3>

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
