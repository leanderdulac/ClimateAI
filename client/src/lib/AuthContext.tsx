/**
 * AuthContext with Supabase Authentication
 * Provides authentication state and methods for the entire app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase, isSupabaseConfigured, getSupabaseClient } from './supabase';
import { buildApiUrl } from './api';
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
  success: string | null;
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
  const BACKEND_AUTH_TIMEOUT_MS = 30000;
  const BACKEND_REGISTER_MAX_ATTEMPTS = 2;

  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const withTimeout = async <T,>(promise: Promise<T>, timeoutMs: number, timeoutMessage: string): Promise<T> => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutId = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs);
    });

    try {
      return await Promise.race([promise, timeoutPromise]);
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  };

  const isTimeoutMessage = (message: string): boolean => {
    return message.toLowerCase().includes('timeout');
  };

  const isNetworkErrorMessage = (message: string): boolean => {
    return (
      message.includes('Failed to fetch') ||
      message.includes('NetworkError') ||
      message.includes('ERR_NAME_NOT_RESOLVED') ||
      message.includes('ERR_CONNECTION') ||
      message.includes('TypeError: Failed to fetch')
    );
  };

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

  // buildApiUrl handles both production (relative URLs) and development (localhost)

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
        setSession({ access_token: accessToken, refresh_token: refreshToken } as any);
      }
    } else {
      // Try to restore Supabase session first
      const client = getSupabaseClient();
      const restoreSession = async () => {
        if (client) {
          try {
            const { data } = await withTimeout(
              client.auth.getSession(),
              5000,
              'Timeout ao restaurar sessão Supabase'
            );
            const currentSession = data?.session;
            if (currentSession?.user) {
              setSession(currentSession);

              try {
                const mappedUser = await withTimeout(
                  mapSupabaseUser(currentSession.user),
                  5000,
                  'Timeout ao carregar perfil do usuário'
                );
                setUser(mappedUser);
              } catch (profileError) {
                console.warn('Falha ao carregar perfil via Supabase, usando fallback local:', profileError);
                setUser({
                  id: currentSession.user.id,
                  email: currentSession.user.email || '',
                  name: currentSession.user.user_metadata?.full_name || '',
                  role: 'user'
                });
              }

              return;
            }
          } catch (sessionError) {
            console.warn('Falha ao restaurar sessão Supabase, seguindo com fallback local:', sessionError);
          }
        }

        // Fallback to legacy localStorage tokens (non-Supabase)
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        if (accessToken && refreshToken) {
          setSession({ access_token: accessToken, refresh_token: refreshToken } as any);
          setUser({
            id: 'temp',
            email: 'user@example.com',
            name: 'User',
            role: 'user'
          });
        }
      };

      restoreSession().finally(() => setIsLoading(false));
      return;
    }

    setIsLoading(false);

    return () => {
      // Cleanup if needed
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      // Tentar login via backend local primeiro (bypass do Supabase)
      const endpoint = buildApiUrl('/api/v1/auth/login');

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        if (response.ok) {
          const data = await response.json();
          // Backend retornou o token com sucesso
          setUser(data.user);
          setSession({ access_token: data.access_token, refresh_token: data.refresh_token } as any);
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          return;
        }

        const payload = await response.json().catch(() => null);
        const backendMessage = payload?.detail || payload?.message || payload?.error;

        if (response.status < 500) {
          throw new Error(typeof backendMessage === 'string' ? backendMessage : 'Falha no login');
        }

        // When backend is reachable but returning 5xx, prefer a clear API error.
        throw new Error(
          typeof backendMessage === 'string' && backendMessage.trim().length > 0
            ? backendMessage
            : 'Servico de autenticacao indisponivel no momento. Tente novamente em instantes.'
        );
      } catch (backendError) {
        if (backendError instanceof Error) {
          if (!isNetworkErrorMessage(backendError.message)) {
            throw backendError;
          }

          throw new Error('Falha de conexao com o servico de autenticacao. Verifique se a API esta online.');
        }

        console.warn('Backend login falhou, tentando fallback Supabase:', backendError);
      }

      // Fallback para Supabase se o backend falhar
      const client = getSupabaseClient();
      if (!client) throw new Error('Supabase não configurado');

      let data: { session: Session | null; user: SupabaseUser | null } | null = null;
      let signInError: Error | null = null;
      try {
        const result = await client.auth.signInWithPassword({ email, password });
        data = result.data;
        if (result.error) {
          throw new Error(result.error.message || 'Falha no login');
        }
      } catch (supabaseNetworkError) {
        const msg =
          supabaseNetworkError instanceof Error
            ? supabaseNetworkError.message
            : String(supabaseNetworkError || '');

        if (isNetworkErrorMessage(msg)) {
          signInError = new Error(
            'Nao foi possivel conectar ao Supabase. Verifique VITE_SUPABASE_URL, DNS e conectividade de rede.'
          );
        } else {
          signInError =
            supabaseNetworkError instanceof Error
              ? supabaseNetworkError
              : new Error('Falha no login');
        }
      }

      if (signInError) throw signInError;
      if (!data.session || !data.user) throw new Error('Sessão inválida');
      setUser(await mapSupabaseUser(data.user));
      setSession(data.session);
      localStorage.setItem('access_token', data.session.access_token);
      localStorage.setItem('refresh_token', data.session.refresh_token ?? '');
    } catch (err) {
      let message = err instanceof Error ? err.message : 'Falha no login';
      if (isNetworkErrorMessage(message)) {
        message = 'Falha de conexao com o servico de autenticacao. Verifique se a API esta online.';
      }
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      if (!userData.name || !userData.email || !userData.password) {
        throw new Error('Todos os campos obrigatórios devem ser preenchidos');
      }

      // Try backend registration first so signup works even when Supabase DNS is unavailable.
      const registerEndpoint = buildApiUrl('/api/v1/auth/register');
      try {
        let registerResponse: Response | null = null;

        for (let attempt = 1; attempt <= BACKEND_REGISTER_MAX_ATTEMPTS; attempt += 1) {
          try {
            registerResponse = await withTimeout(
              fetch(registerEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  email: userData.email,
                  full_name: userData.name,
                  password: userData.password,
                  organization: userData.company || ''
                })
              }),
              BACKEND_AUTH_TIMEOUT_MS,
              'Timeout ao registrar usuario'
            );
            break;
          } catch (registerAttemptError) {
            const isLastAttempt = attempt === BACKEND_REGISTER_MAX_ATTEMPTS;
            const message = registerAttemptError instanceof Error ? registerAttemptError.message : '';

            if (!isTimeoutMessage(message) || isLastAttempt) {
              throw registerAttemptError;
            }
          }
        }

        if (!registerResponse) {
          throw new Error('Falha no cadastro');
        }

        if (registerResponse.ok) {
          const loginEndpoint = buildApiUrl('/api/v1/auth/login');
          const loginResponse = await withTimeout(
            fetch(loginEndpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: userData.email, password: userData.password })
            }),
            BACKEND_AUTH_TIMEOUT_MS,
            'Timeout ao autenticar apos cadastro'
          );

          if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            setUser(loginData.user);
            setSession({ access_token: loginData.access_token, refresh_token: loginData.refresh_token } as any);
            localStorage.setItem('access_token', loginData.access_token);
            localStorage.setItem('refresh_token', loginData.refresh_token);
            setSuccess('Cadastro realizado com sucesso!');
            return;
          }

          throw new Error('Cadastro realizado. Faca login para continuar.');
        }

        const payload = await registerResponse.json().catch(() => null);
        const backendMessage = payload?.detail || payload?.message || payload?.error;

        if (registerResponse.status < 500) {
          throw new Error(typeof backendMessage === 'string' ? backendMessage : 'Falha no cadastro');
        }

        throw new Error(
          typeof backendMessage === 'string' && backendMessage.trim().length > 0
            ? backendMessage
            : 'Servico de cadastro indisponivel no momento. Tente novamente em instantes.'
        );
      } catch (backendRegisterError) {
        if (backendRegisterError instanceof Error && !isNetworkErrorMessage(backendRegisterError.message)) {
          throw backendRegisterError;
        }
      }

      const client = getSupabaseClient();
      if (!client) throw new Error('Supabase não configurado');

      const { data, error } = await withTimeout(
        client.auth.signUp({
          email: userData.email,
          password: userData.password,
          options: {
            data: {
              full_name: userData.name,
              company_name: userData.company || '',
              role: 'user',
            },
          },
        }),
        10000,
        'Timeout ao registrar no Supabase'
      );
      if (error) throw new Error(error.message || 'Falha no cadastro');
      if (data.session) {
        localStorage.setItem('access_token', data.session.access_token);
        localStorage.setItem('refresh_token', data.session.refresh_token ?? '');
        setSession(data.session);
        if (data.user) setUser(await mapSupabaseUser(data.user));
      }
      setSuccess('Cadastro realizado com sucesso! Verifique seu e-mail para ativar a conta.');
    } catch (err) {
      let message = err instanceof Error ? err.message : 'Falha no cadastro';
      if (isNetworkErrorMessage(message)) {
        message = 'Falha de conexao com o servico de cadastro. Verifique se a API esta online.';
      }
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const client = getSupabaseClient();
      if (client) {
        await client.auth.signOut();
      }
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
    setSuccess(null);

    // Redirect URL after password reset — must match an existing route
    const resetRedirectUrl = `${window.location.origin}/auth`;

    try {
      // 1. Try backend endpoint first
      const endpoint = buildApiUrl('/api/v1/auth/forgot-password');
      try {
        const response = await withTimeout(
          fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
          }),
          BACKEND_AUTH_TIMEOUT_MS,
          'Timeout ao solicitar recuperacao de senha pelo backend'
        );
        if (response.ok) {
          setSuccess('Se o e-mail estiver cadastrado, voce recebera as instrucoes de recuperacao.');
          return;
        }
      } catch (backendErr) {
        // Backend unreachable — fall through to Supabase
        const msg = backendErr instanceof Error ? backendErr.message : '';
        if (!isNetworkErrorMessage(msg) && !msg.includes('Timeout')) {
          throw backendErr;
        }
      }

      // 2. Fallback to Supabase
      const client = getSupabaseClient();
      if (!client) {
        // Neither backend nor Supabase available — show generic safe message
        setSuccess('Se o e-mail estiver cadastrado, voce recebera as instrucoes de recuperacao.');
        return;
      }

      const { error } = await withTimeout(
        client.auth.resetPasswordForEmail(email, {
          redirectTo: resetRedirectUrl,
        }),
        10000,
        'Timeout ao solicitar recuperacao de senha'
      );

      // Supabase returns error for unregistered emails too — show safe message regardless
      if (error && !isNetworkErrorMessage(error.message)) {
        console.warn('Supabase resetPassword error:', error.message);
      }

      // Always show safe success message (security best practice — don't reveal if email exists)
      setSuccess('Se o e-mail estiver cadastrado, voce recebera as instrucoes de recuperacao.');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao solicitar reset de senha';
      if (isNetworkErrorMessage(message) || message.includes('Timeout')) {
        // Network failure — still show safe success message
        setSuccess('Se o e-mail estiver cadastrado, voce recebera as instrucoes de recuperacao.');
      } else {
        setError(message);
        throw new Error(message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const client = getSupabaseClient();
      if (!client || !user) throw new Error('Usuário não autenticado');

      const { error } = await client
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
    success,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Export for backwards compatibility
export { AuthContext };
