import React, { useState } from 'react';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';
import { useAuth } from './AuthContext';

interface AuthControllerProps {
  onAuthSuccess?: () => void;
}

const AuthController: React.FC<AuthControllerProps> = ({ onAuthSuccess }) => {
  // State to control which form to display
  const [showSignup, setShowSignup] = useState(false);
  
  // Get auth functions from context
  const { login, signup } = useAuth();

  // Switch to signup form
  const handleShowSignup = () => {
    setShowSignup(true);
  };
  
  // Switch to login form
  const handleShowLogin = () => {
    setShowSignup(false);
  };
  
  // Handle login submit
  const handleLogin = (username: string, password: string) => {
    login(username, password);
    if (onAuthSuccess) {
      onAuthSuccess();
    }
  };
  
  // Handle signup submit
  const handleSignup = (userData: any) => {
    signup(userData);
    if (onAuthSuccess) {
      onAuthSuccess();
    }
  };

  return (
    <div style={{
      backgroundColor: '#F2F0EF',
      minHeight: '100vh',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }}>
      <div style={{
        borderRadius: '10px',
        padding: '2rem',
        width: '100%',
        maxWidth: '800px',
      }}>
        {showSignup ? (
          <SignupForm 
            onBackToLogin={handleShowLogin} 
            onSignup={handleSignup} 
          />
        ) : (
          <LoginForm 
            onCreateAccount={handleShowSignup} 
            onLogin={handleLogin}
          />
        )}
      </div>
    </div>
  );
};

export default AuthController;