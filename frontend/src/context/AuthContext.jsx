import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser, logout as apiLogout } from '../services/api';

/**
 * AuthContext — manages JWT token, current-user state, and auth operations.
 *
 * Token & user are persisted in localStorage so a page-refresh preserves
 * the authenticated session.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true until we've verified the session
  const [initialised, setInitialised] = useState(false);

  // On mount, hydrate user from localStorage + verify against backend
  useEffect(() => {
    const bootstrap = async () => {
      const storedToken = localStorage.getItem('trustmatch_token');
      const storedUser = localStorage.getItem('trustmatch_user');

      if (storedToken && storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          // Verify token is still valid by calling /auth/users/me
          const freshUser = await getCurrentUser();
          setUser(freshUser);
        } catch (err) {
          // Token invalid or expired — clear storage
          console.warn('[Auth] Token invalid or expired, clearing session.');
          localStorage.removeItem('trustmatch_token');
          localStorage.removeItem('trustmatch_user');
          setUser(null);
        }
      }
      setLoading(false);
      setInitialised(true);
    };

    bootstrap();
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    localStorage.setItem('trustmatch_token', data.access_token);

    // Fetch the full user object so the UI has the name/email
    const currentUser = await getCurrentUser();
    localStorage.setItem('trustmatch_user', JSON.stringify(currentUser));
    setUser(currentUser);

    return { token: data.access_token, user: currentUser };
  }, []);

  const register = useCallback(async (name, email, password) => {
    const data = await apiRegister(name, email, password);
    localStorage.setItem('trustmatch_token', data.access_token);

    const currentUser = await getCurrentUser();
    localStorage.setItem('trustmatch_user', JSON.stringify(currentUser));
    setUser(currentUser);

    return { token: data.access_token, user: currentUser };
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
  }, []);

  const value = {
    user,
    loading,         // still checking session on initial load
    initialised,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
