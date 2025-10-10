import React, { createContext, useState, useContext, ReactNode } from "react";

// Define the shape of your user object
interface User {
  username: string;
  section: string;
  // Add any other user properties you need, like role or token
}

// Define the values the context will provide
interface AuthContextType {
  user: User | null;
  login: (userData: User) => void;
  logout: () => void;
}

// Create the context with a default undefined value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the Provider component that will wrap your app
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  // Function to call upon successful login
  const login = (userData: User) => {
    setUser(userData);
    // You would typically also save a JWT token to localStorage here
  };

  // Function to call to log the user out
  const logout = () => {
    setUser(null);
    // And clear the token from localStorage
  };

  const value = { user, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Create a custom hook for easy access to the context in other components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};