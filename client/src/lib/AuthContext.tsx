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

  // Initialize auth state
  useEffect(() => {
    if (!isSupabaseConfigured() || !supabase) {
      console.warn('Supabase not configured, using fallback auth');
      setIsLoading(false);
      return;
    }

    // Get initial session
    const initAuth = async () => {
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession();

        if (currentSession?.user) {
          setSession(currentSession);
          const mappedUser = await mapSupabaseUser(currentSession.user);
          setUser(mappedUser);
        }
      } catch (err) {
        console.error('Error initializing auth:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('Auth state changed:', event);

        if (newSession?.user) {
          setSession(newSession);
          const mappedUser = await mapSupabaseUser(newSession.user);
          setUser(mappedUser);
        } else {
          setSession(null);
          setUser(null);
        }

        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      if (!supabase) {
        throw new Error('Supabase não configurado');
      }

      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        throw new Error(authError.message === 'Invalid login credentials'
          ? 'E-mail ou senha incorretos'
          : authError.message);
      }

      if (data.user) {
        const mappedUser = await mapSupabaseUser(data.user);
        setUser(mappedUser);
        setSession(data.session);
      }
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
      if (!supabase) {
        throw new Error('Supabase não configurado');
      }

      // Validate input
      if (!userData.name || !userData.email || !userData.password) {
        throw new Error('Todos os campos obrigatórios devem ser preenchidos');
      }

      if (userData.password.length < 6) {
        throw new Error('A senha deve ter pelo menos 6 caracteres');
      }

      // Sign up with Supabase
      const { data, error: authError } = await supabase.auth.signUp({
        email: userData.email,
        password: userData.password,
        options: {
          data: {
            full_name: userData.name,
            company_name: userData.company || '',
          },
        },
      });

      if (authError) {
        if (authError.message.includes('already registered')) {
          throw new Error('Este e-mail já está cadastrado');
        }
        throw new Error(authError.message);
      }

      // Update profile with additional info
      if (data.user) {
        await supabase.from('profiles').upsert({
          id: data.user.id,
          email: userData.email,
          full_name: userData.name,
          company_name: userData.company || '',
        });

        const mappedUser = await mapSupabaseUser(data.user);
        setUser(mappedUser);
        setSession(data.session);
      }
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
      if (supabase) {
        const { error: authError } = await supabase.auth.signOut();
        if (authError) {
          console.error('Logout error:', authError);
        }
      }

      setUser(null);
      setSession(null);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    setError(null);

    try {
      if (!supabase) {
        throw new Error('Supabase não configurado');
      }

      const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (authError) {
        throw new Error(authError.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao enviar e-mail';
      setError(message);
      throw new Error(message);
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    setError(null);

    try {
      if (!supabase || !user) {
        throw new Error('Usuário não autenticado');
      }

      const { error: updateError } = await supabase
        .from('profiles')
        .update({
          full_name: data.name,
          company_name: data.company,
          avatar_url: data.avatar,
        })
        .eq('id', user.id);

      if (updateError) {
        throw new Error(updateError.message);
      }

      // Update local state
      setUser(prev => prev ? { ...prev, ...data } : null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao atualizar perfil';
      setError(message);
      throw new Error(message);
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
