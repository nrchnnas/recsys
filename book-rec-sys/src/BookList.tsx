import React from 'react';
import { IoIosArrowBack } from "react-icons/io";
import BookDropdown from './BookDropdown'; // Import our updated component

type Book = {
    title: string;
    // Optional additional book properties
    author?: string;
    isbn?: string;
};

type BookRenderProps = {
    book: Book;
};

type BookListProps = {
    title: string;
    books: Book[];
    onBackClick: () => void;
    className?: string;
    customStyle?: React.CSSProperties;
    bookRenderItem?: React.ComponentType<BookRenderProps>;
};

// Updated book render item with improved layout
const DefaultBookRenderItem: React.FC<BookRenderProps> = ({ book }) => (
    <div 
        key={book.title}
        style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '1rem',
            backgroundColor: 'white',
            border: '1px solid #ccc',
            borderRadius: '8px',
            marginBottom: '0.5rem',
            position: 'relative', // Important for proper dropdown positioning
        }}
    >
        <span style={{ 
            color: '#0F9F90',
            fontWeight: 500,
            fontSize: '1.1rem'
        }}>
            {book.title}
        </span>
        <BookDropdown bookTitle={book.title} />
    </div>
);

const BookList: React.FC<BookListProps> = ({ 
    title, 
    books, 
    onBackClick, 
    customStyle = {},
    bookRenderItem: BookRenderItem = DefaultBookRenderItem
}) => {
    return (
        <div>
            <div className="section-header">
                <button
                    onClick={onBackClick}
                    className="back-button"
                >
                    <IoIosArrowBack />
                </button>
                <h3>{title} Books</h3>
            </div>

            <div 
                className="genre-grid" 
                style={{ 
                    gridTemplateColumns: '1fr', 
                    maxWidth: '100%',
                    ...customStyle,
                    position: 'relative', // Important for proper dropdown positioning
                }}
            >
                {books.map((book) => (
                    <BookRenderItem key={book.title} book={book} />
                ))}
            </div>
        </div>
    );
};

export default BookList;