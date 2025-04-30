import React from 'react';
import { IoIosArrowBack } from "react-icons/io";
import { MdOutlineBookmarkAdd } from "react-icons/md";

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
            marginBottom: '0.5rem'
        }}
    >
        <span>{book.title}</span>
        <button 
            style={{
                background: 'none',
                border: 'none',
                color: '#0F9F90',
                cursor: 'pointer'
            }}
        >
            <MdOutlineBookmarkAdd />
        </button>
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
            {/* Updated to use section-header class */}
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
                    ...customStyle
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