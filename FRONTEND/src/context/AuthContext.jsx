import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('brandguard_token'));
  const [loading, setLoading] = useState(true);

  // Initialize and verify authentication state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('brandguard_token');
      if (storedToken) {
        try {
          const response = await api.get('/auth/me');
          if (response.data.success && response.data.user) {
            setUser(response.data.user);
          } else {
            logout();
          }
        } catch (error) {
          console.error('Failed to restore user session:', error);
          logout();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (identifier, password) => {
    try {
      const response = await api.post('/auth/login', { identifier, password });
      if (response.data.success) {
        const { user, token } = response.data;
        setUser(user);
        setToken(token);
        localStorage.setItem('brandguard_token', token);
        localStorage.setItem('brandguard_user', JSON.stringify(user));
        return { success: true, user };
      }
      return { success: false, error: response.data.error || 'Login failed' };
    } catch (error) {
      const msg = error.response?.data?.error || error.message || 'Server connection error';
      return { success: false, error: msg };
    }
  };

  const register = async ({ username, email, password, role, full_name }) => {
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password,
        role,
        full_name,
      });
      if (response.data.success) {
        const { user, token } = response.data;
        setUser(user);
        setToken(token);
        localStorage.setItem('brandguard_token', token);
        localStorage.setItem('brandguard_user', JSON.stringify(user));
        return { success: true, user };
      }
      return { success: false, error: response.data.error || 'Registration failed' };
    } catch (error) {
      const msg = error.response?.data?.error || error.message || 'Server connection error';
      return { success: false, error: msg };
    }
  };

  const logout = () => {
    localStorage.removeItem('brandguard_token');
    localStorage.removeItem('brandguard_user');
    setUser(null);
    setToken(null);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    isCreator: user?.role === 'creator',
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
