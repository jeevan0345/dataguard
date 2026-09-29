import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Role } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isEngineer: boolean;
  isViewer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('dataguard_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('dataguard_token');
      if (storedToken) {
        try {
          const profile = await api.auth.getMe();
          setUser(profile);
          setToken(storedToken);
        } catch (err: any) {
          console.warn('Session expired or invalid token. Redirecting to login view.');
          localStorage.removeItem('dataguard_token');
          setUser(null);
          setToken(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await api.auth.login(email, pass);
    localStorage.setItem('dataguard_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem('dataguard_token');
    setToken(null);
    setUser(null);
  };

  const role: Role = user?.role || 'VIEWER';
  const isAdmin = role === 'ADMIN' || !!user?.is_superuser;
  const isEngineer = isAdmin || role === 'DATA_ENGINEER';
  const isViewer = true;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAdmin,
        isEngineer,
        isViewer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
