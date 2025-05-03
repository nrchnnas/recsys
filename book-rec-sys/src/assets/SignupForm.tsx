import React, { useState } from 'react';
import { MdOutlineBookmarkAdd } from "react-icons/md";

interface Book {
  title: string;
}

interface SignupFormProps {
  onBackToLogin: () => void; // Function to switch back to login view
  onSignup?: (userData: any) => void; // Optional callback for signup
}

const SignupForm: React.FC<SignupFormProps> = ({ onBackToLogin, onSignup }) => {
  // State for user credentials
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // State for form steps
  const [step, setStep] = useState(1);
  
  // State for user preferences
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [favoriteBooks, setFavoriteBooks] = useState<Book[]>([]);
  const [currentBook, setCurrentBook] = useState('');
  
  // Error state
  const [error, setError] = useState('');

  // List of available genres - matching the ones in your app
  const genres = [
    "Children", "Comics & Graphic", "Mystery, Thriller & Crime", "Poetry",
    "Fantasy & Paranormal", "History & Biography", "Romance", "Young Adult"
  ];
  
  // Toggle genre selection
  const toggleGenre = (genre: string) => {
    if (selectedGenres.includes(genre)) {
      setSelectedGenres(selectedGenres.filter(g => g !== genre));
    } else {
      setSelectedGenres([...selectedGenres, genre]);
    }
  };
  
  // Add a book to favorites
  const addBook = () => {
    if (currentBook.trim()) {
      setFavoriteBooks([...favoriteBooks, { 
        title: currentBook,  
      }]);
      setCurrentBook('');
    }
  };
  
  // Remove a book from favorites
  const removeBook = (bookTitle: string) => {
    setFavoriteBooks(favoriteBooks.filter(book => book.title !== bookTitle));
  };
  
  // Handle credentials submission
  const handleCredentialsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate inputs
    if (!username.trim() || !password.trim()) {
      setError('Username and password are required');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Move to next step
    setError('');
    setStep(2);
  };
  
  // Handle final submission
  const handlePreferencesSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Add the current book if input is not empty
    if (currentBook.trim()) {
      addBook();
    }
    
    // Create user with preferences
    const userData = {
      username,
      email,
      password,
      preferences: {
        genres: selectedGenres,
        favoriteBooks
      }
    };
    
    // Call the onSignup callback if provided
    if (onSignup) {
      onSignup(userData);
    }
    
    console.log('User signup data:', userData);
  };
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      width: '100%'
    }}>
      <h1 style={{ 
        color: '#0F9F90', 
        fontSize: '2.5rem', 
        marginBottom: '0.5rem',
        textAlign: 'center'
      }}>
        Creating A New Account
      </h1>
      
      <h2 style={{ 
        color: '#0F9F90', 
        fontSize: '1.2rem', 
        fontWeight: 'normal',
        marginBottom: '3rem',
        textAlign: 'center'
      }}>
        let's get to know each other more
      </h2>
      
      {step === 1 ? (
        <form onSubmit={handleCredentialsSubmit} style={{ width: '100%', maxWidth: '400px' }}>
          {error && (
            <div style={{ 
              color: 'red', 
              marginBottom: '1rem', 
              textAlign: 'center' 
            }}>
              {error}
            </div>
          )}
          
          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="username" 
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #ccc',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="email" 
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #ccc',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <label 
              htmlFor="password" 
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #ccc',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '2rem' }}>
            <label 
              htmlFor="confirmPassword" 
              style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: '#333'
              }}
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid #ccc',
                boxSizing: 'border-box'
              }}
            />
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <button
            type="button"
            onClick={onBackToLogin}
            className="btn-secondary"
            >
            Back to Login
            </button>
            
            <button
            type="submit"
            className="btn-primary"
            >
            Next
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handlePreferencesSubmit} style={{ width: '100%', maxWidth: '800px' }}>
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ 
              color: '#0F9F90', 
              fontSize: '1.2rem', 
              marginBottom: '0.5rem',
              fontWeight: 'normal'
            }}>
              What genres do you like?
            </h3>
            <p style={{ color: '#333', marginBottom: '1rem' }}>Select all the genres you like</p>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
              gap: '1rem',
              marginBottom: '2rem'
            }}>
              {genres.map(genre => (
                <button
                  key={genre}
                  type="button"
                  onClick={() => toggleGenre(genre)}
                  style={{
                    padding: '1rem',
                    border: `1px solid ${selectedGenres.includes(genre) ? '#0F9F90' : '#CFC9B3'}`,
                    borderRadius: '8px',
                    backgroundColor: selectedGenres.includes(genre) ? '#0F9F90' : 'white',
                    color: selectedGenres.includes(genre) ? 'white' : 'black',
                    cursor: 'pointer',
                    textAlign: 'center',
                    fontWeight: 'normal'
                  }}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>
          
          <div>
            <h3 style={{ 
              color: '#0F9F90', 
              fontSize: '1.2rem', 
              marginBottom: '0.5rem',
              fontWeight: 'normal'
            }}>
              What books have you read that you liked?
            </h3>
            <p style={{ color: '#333', marginBottom: '1rem' }}>Enter your book titles and star ratings</p>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                marginBottom: '1rem',
                gap: '0.5rem'
              }}>
                <input
                  type="text"
                  value={currentBook}
                  onChange={(e) => setCurrentBook(e.target.value)}
                  placeholder="Enter a book title"
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #ccc'
                  }}
                />
                
                <button
                  type="button"
                  onClick={addBook}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#0F9F90',
                    cursor: 'pointer'
                  }}
                >
                  <MdOutlineBookmarkAdd size={24} />
                </button>
              </div>
              
              {favoriteBooks.map((book, index) => (
                <div 
                  key={index}
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem',
                    backgroundColor: 'white',
                    border: '1px solid #ccc',
                    borderRadius: '8px',
                    marginBottom: '0.5rem'
                  }}
                >
                  <span>{book.title}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    
                    <button
                      type="button"
                      onClick={() => removeBook(book.title)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'red',
                        cursor: 'pointer',
                        fontSize: '1.25rem',
                        padding: '0 0.5rem'
                      }}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '2rem' }}>
            <button
                type="button"
                onClick={() => setStep(1)}
                className="btn-secondary"
                >
                Back
            </button>
            
            <button
                type="submit"
                className="btn-primary"
                >
                Submit
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default SignupForm;