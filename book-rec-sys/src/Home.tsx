import { RiBookShelfLine } from "react-icons/ri";
import { FaBookBookmark } from "react-icons/fa6";
import { IoIosArrowForward } from "react-icons/io";
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
            <h3 style={{ fontStyle: "italic", marginTop: "2rem" }}>Search By Genre</h3>
            <GenreGrid genres={genres} onGenreClick={handleGenreClick} />
        </div>
    );
}

function Panel() {
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

            <ul className="panel-links">
                <li>
                    <RiBookShelfLine className="icon" />
                    <span>View Your Shelves</span>
                    <IoIosArrowForward className="icon"/>
                </li>
                <li>
                    <FaBookBookmark className="icon" />
                    <span>View Your Reviews</span>
                    <IoIosArrowForward className="icon"/>
                </li>
            </ul>

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
                <button className="panel-button">Add New Current Read</button>
                <button className="panel-button">Add New Review</button>
            </div>
        </div>
            </div>
    );
}

export default Title;
export { Panel, GenreSection };