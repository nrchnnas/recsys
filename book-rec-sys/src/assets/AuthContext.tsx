import React, { createContext, useState, useContext, ReactNode } from 'react';

// Define the shape of our user object
interface User {
  username: string;
  email?: string;
  preferences?: {
    genres: string[];
    favoriteBooks: Array<{
      title: string;
      rating: number;
    }>;
  };
}

// Define the shape of our context
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => void;
  logout: () => void;
  signup: (userData: User) => void;
}

// Create the context with a default value
const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
  signup: () => {},
});

// Create a provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // State for the user
  const [user, setUser] = useState<User | null>(null);
  
  // Derived state for authentication status
  const isAuthenticated = user !== null;

  // Login function
  const login = (username: string, password: string) => {
    // In a real app, this would validate against a backend
    console.log('Logging in:', username);
    
    // For now, just set a basic user
    setUser({
      username,
      preferences: {
        genres: [],
        favoriteBooks: []
      }
    });
  };

  // Logout function
  const logout = () => {
    console.log('Logging out');
    setUser(null);
  };

  // Signup function
  const signup = (userData: User) => {
    console.log('Signing up:', userData);
    setUser(userData);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        login,
        logout,
        signup,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for using the auth context
export const useAuth = () => useContext(AuthContext);

export default AuthContext;