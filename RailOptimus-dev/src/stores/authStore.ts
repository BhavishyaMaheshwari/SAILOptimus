import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

// --- Simplified User interface ---
export interface User {
  _id: string;
  name: string;
  username: string;
}

// --- Simplified AuthState interface ---
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (payload: {
    name: string;
    section: string;
    username: string;
    password: string;
    passwordConfirm: string;
  }) => Promise<boolean>;
  logout: () => void;
}

// --- API Configuration ---
const API_URL = 'http://localhost:5005/api/users';

// --- Simplified Zustand Store ---
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      /**
       * Logs in a user by calling the backend API.
       */
      login: async (username, password) => {
        try {
          const response = await axios.post(`${API_URL}/login`, { username, password });
          
          if (response.data.status === 'success') {
            const { user, token } = response.data.data;
            set({ user, token, isAuthenticated: true });
            return true;
          }
          return false;
        } catch (error: any) {
          console.error("Login failed:", error.response?.data?.message || error.message);
          throw new Error(error.response?.data?.message || 'Login failed. Please check your credentials.');
        }
      },

      /**
       * Logs the user out by clearing their data from the state.
       */
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },
      /**
       * Registers a new user via the backend API.
       */
      signup: async (payload) => {
        try {
          const response = await axios.post(`${API_URL}/signup`, payload);

          if (response.data.status === 'success') {
            const { user, token } = response.data.data;
            set({ user, token, isAuthenticated: true });
            return true;
          }
          return false;
        } catch (error: any) {
          console.error('Signup failed:', error.response?.data?.message || error.message);
          throw new Error(error.response?.data?.message || 'Signup failed.');
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);