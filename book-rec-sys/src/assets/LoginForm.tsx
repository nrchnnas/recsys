import React, { useState } from 'react';

interface LoginFormProps {
  onCreateAccount: () => void;
  onLogin: (username: string, password: string) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onCreateAccount, onLogin }) => {
  // State for form fields
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }
    
    // Call the login callback
    onLogin(username, password);
  };
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%'
    }}>
      <h1 style={{ 
        color: '#0F9F90', 
        fontSize: '2.5rem', 
        marginBottom: '0.5rem',
        textAlign: 'center'
      }}>
        What Should I Read Next?
      </h1>
      
      <h2 style={{ 
        color: '#0F9F90', 
        fontSize: '1.2rem', 
        fontWeight: 'normal',
        marginBottom: '3rem',
        textAlign: 'center'
      }}>
        let us help you find your next book
      </h2>
      
      <h3 style={{ 
        color: '#0F9F90', 
        fontSize: '1.5rem', 
        fontWeight: 'normal',
        marginBottom: '2rem',
        textAlign: 'center'
      }}>
        Sign Up / Login
      </h3>
      
      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '400px' }}>
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
              textAlign: 'center',
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
        
        <div style={{ marginBottom: '2rem' }}>
          <label 
            htmlFor="password" 
            style={{ 
              display: 'block', 
              marginBottom: '0.5rem',
              textAlign: 'center',
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
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <button
            type="submit"
            style={{
              backgroundColor: '#0F9F90',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              padding: '0.75rem 2rem',
              fontSize: '1rem',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Login
          </button>
          
            <button
                type="button"
                onClick={onCreateAccount}
                className="btn-secondary"
                >
                Create Account
            </button>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;