import { createContext, useContext, useState } from 'react';
import api from '../api/index.js';

const AuthContext = createContext(null);

const COOKIE_NAME = 'tqa_user';

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? JSON.parse(decodeURIComponent(match[1])) : null;
};

const setCookie = (name, value) => {
  document.cookie = `${name}=${encodeURIComponent(JSON.stringify(value))}; path=/; SameSite=Lax`;
};

const deleteCookie = (name) => {
  document.cookie = `${name}=; path=/; max-age=0`;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => getCookie(COOKIE_NAME));

  const login = async (email, password) => {
    const response = await api.post('/api/login', { email, password });
    const userData = { email };
    setUser(userData);
    setCookie(COOKIE_NAME, userData);
    return response;
  };

  const signup = async (firstname, lastname, email, password) => {
    const response = await api.post('/api/signup', { firstname, lastname, email, password });
    const userData = { email, firstname, lastname };
    setUser(userData);
    setCookie(COOKIE_NAME, userData);
    return response;
  };

  const logout = async () => {
    await api.post('/api/logout');
    setUser(null);
    deleteCookie(COOKIE_NAME);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
