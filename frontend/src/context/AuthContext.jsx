import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('nagarnexus_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('nagarnexus_token') || null);
  const [loading, setLoading] = useState(Boolean(token));
  const [theme, setTheme] = useState(() => localStorage.getItem('nagarnexus_theme') || 'dark');
  const [activeDatasetId, setActiveDatasetId] = useState(null);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('nagarnexus_theme', theme);
  }, [theme]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let mounted = true;
    api
      .get('/auth/me')
      .then((res) => {
        if (mounted) {
          setUser(res.data);
          localStorage.setItem('nagarnexus_user', JSON.stringify(res.data));
        }
      })
      .catch(() => {
        if (mounted) {
          localStorage.removeItem('nagarnexus_token');
          localStorage.removeItem('nagarnexus_user');
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [token]);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('nagarnexus_token', access_token);
    localStorage.setItem('nagarnexus_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (payload) => {
    const res = await api.post('/auth/register', payload);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('nagarnexus_token', access_token);
    localStorage.setItem('nagarnexus_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('nagarnexus_token');
    localStorage.removeItem('nagarnexus_user');
    setToken(null);
    setUser(null);
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        token,
        loading,
        login,
        register,
        logout,
        theme,
        setTheme,
        toggleTheme,
        activeDatasetId,
        setActiveDatasetId,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

