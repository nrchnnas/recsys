import { RiBookShelfLine } from "react-icons/ri";
import { FaBookBookmark } from "react-icons/fa6";
import { useState } from 'react';
import GenreGrid from './GenreGrid';

const genres = [
    "Children",
    "Comics & Graphic",
    "Mystery, Thriller & Crime",
    "Poetry",
    "Fantasy & Paranormal",
    "History & Biography",
    "Romance",
    "Young Adult"
];

function Title() {
    return (
        <div>
            <h1>What Should I Read Today?</h1>
            <h2>let us help you find your next book</h2>
        </div>
    );
}

function GenreSection() {
    const handleGenreClick = (genre: string) => {
        console.log("Genre selected:", genre);
    };

    return (
        <div className="main-container">
            {/* Updated to use section-header class */}
            <div className="section-header">
                <h3>Search By Genre</h3>
            </div>
            <GenreGrid genres={genres} onGenreClick={handleGenreClick} />
        </div>
    );
}

function Panel({ onViewShelvesClick }: { onViewShelvesClick: () => void }) {
    const [isChecked, setIsChecked] = useState(false);
    const [inputValue, setInputValue] = useState('');
    const [bookTitle, setBookTitle] = useState('');

    const handleCheckboxChange = () => {
        // If they check the box, reset all
        if (!isChecked) {
            setIsChecked(true);
        } else {
            // Reset everything
            setIsChecked(false);
            setInputValue('');
            setBookTitle('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && inputValue.trim() !== '') {
            setBookTitle(inputValue.trim());
        }
    };

    return (
        <div className="container"> 
            <div id="panel">
            <h2>Your Stats</h2>

            <div className="currently-reading">
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={handleCheckboxChange}
                    />
                    Currently Reading
                </label>

                {!bookTitle ? (
                    <input
                        type="text"
                        placeholder="Enter book title"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        style={{ marginTop: '0.5rem', width: '85%' }}
                    />
                ) : (
                    <p>{bookTitle}</p>
                )}
            </div>
            
            <div className="panel-actions">
                <button className="panel-button" onClick={onViewShelvesClick} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <RiBookShelfLine className="icon" />
                    View Your Shelves
                    </span>
                </button>

                <button className="panel-button" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FaBookBookmark className="icon" />
                    View Your Reviews
                    </span>
                </button>

                <button className="panel-button">Add New Review</button>
                </div>

            </div>
        </div>
    );
}

export default Title;
export { Panel, GenreSection };