import React, { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div 
      className="auth-layout"
      style={{
        backgroundColor: '#F2F0EF',
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem'
      }}
    >
      <div 
        className="auth-container"
        style={{
          backgroundColor: 'white',
          borderRadius: '10px',
          padding: '2rem',
          width: '100%',
          maxWidth: '800px',
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default AuthLayout;