/**
 * AuthContext with Supabase Authentication
 * Provides authentication state and methods for the entire app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase, isSupabaseConfigured } from './supabase';
import type { User as SupabaseUser, Session } from '@supabase/supabase-js';

// User type for the app
interface User {
  id: string;
  email: string;
  name?: string;
  company?: string;
  avatar?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  company?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Convert Supabase user to app user
  const mapSupabaseUser = async (supabaseUser: SupabaseUser): Promise<User> => {
    // Get profile from profiles table
    if (supabase) {
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', supabaseUser.id)
        .single();

      if (profile) {
        return {
          id: supabaseUser.id,
          email: supabaseUser.email || '',
          name: profile.full_name || supabaseUser.user_metadata?.full_name || '',
          company: profile.company_name || '',
          avatar: profile.avatar_url || '',
          role: profile.role || 'user',
        };
      }
    }

    // Fallback to basic user info
    return {
      id: supabaseUser.id,
      email: supabaseUser.email || '',
      name: supabaseUser.user_metadata?.full_name || '',
    };
  };

  // Get status of API (development/production)
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  // Initialize auth state
  useEffect(() => {
    // Check if using mock data
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (useMockData) {
      // Check for stored mock tokens
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');

      if (accessToken === 'mock-access-token' && refreshToken === 'mock-refresh-token') {
        // Set mock user
        setUser({
          id: 'mock-user-1',
          email: 'user@example.com',
          name: 'Mock User',
          company: 'Mock Company',
          role: 'user'
        });
        setSession({ access_token: accessToken, refresh_token: refreshToken });
      }
    } else {
      // Check for stored tokens
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');

      if (accessToken && refreshToken) {
        // TODO: Validate token with backend
        setSession({ access_token: accessToken, refresh_token: refreshToken });
        // For now, set a basic user - in production you'd decode the JWT
        setUser({
          id: 'temp',
          email: 'user@example.com',
          name: 'User',
          role: 'user'
        });
      }
    }

    setIsLoading(false);

    return () => {
      // Cleanup if needed
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw new Error(error.message || 'Falha no login');
      if (!data.session || !data.user) throw new Error('Sessão inválida');
      setUser(await mapSupabaseUser(data.user));
      setSession(data.session);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha no login';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    setIsLoading(true);
    setError(null);
    try {
      if (!userData.name || !userData.email || !userData.password) {
        throw new Error('Todos os campos obrigatórios devem ser preenchidos');
      }
      const { data, error } = await supabase.auth.signUp({
        email: userData.email,
        password: userData.password,
        options: {
          data: {
            full_name: userData.name,
            company_name: userData.company || '',
            role: 'user',
          },
        },
      });
      if (error) throw new Error(error.message || 'Falha no cadastro');
      setError('Cadastro realizado com sucesso! Verifique seu e-mail para ativar a conta.');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha no cadastro';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setSession(null);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    setIsLoading(true);
    setError(null);

    try {
      if (!supabase) throw new Error('Supabase não disponível');

      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });

      if (error) throw error;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao solicitar reset de senha';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    setIsLoading(true);
    setError(null);

    try {
      if (!supabase || !user) throw new Error('Usuário não autenticado');

      const { error } = await supabase
        .from('profiles')
        .update({
          full_name: data.name,
          company_name: data.company,
          avatar_url: data.avatar,
          updated_at: new Date().toISOString(),
        })
        .eq('id', user.id);

      if (error) throw error;

      // Update local state
      setUser(prev => prev ? { ...prev, ...data } : null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao atualizar perfil';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    session,
    login,
    register,
    logout,
    resetPassword,
    updateProfile,
    isLoading,
    isAuthenticated: !!user,
    error,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Export for backwards compatibility
export { AuthContext };
