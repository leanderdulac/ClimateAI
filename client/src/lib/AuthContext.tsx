/**
 * AuthContext with Supabase Authentication
 * Provides authentication state and methods for the entire app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase, isSupabaseConfigured, getSupabaseClient } from './supabase';
import { buildApiUrl } from './api/client';
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

interface BackendUserPayload {
  id: string;
  email: string;
  full_name?: string;
  name?: string;
  organization?: string;
  company?: string;
  role?: string;
  avatar?: string;
}

const MIN_PASSWORD_LENGTH = 8;

function mapBackendUser(data: BackendUserPayload): User {
  return {
    id: data.id,
    email: data.email,
    name: data.full_name || data.name,
    company: data.organization || data.company,
    role: data.role,
    avatar: data.avatar,
  };
}

function assertPasswordPolicy(password: string): void {
  if (password.length < MIN_PASSWORD_LENGTH) {
    throw new Error(`A senha deve ter no mínimo ${MIN_PASSWORD_LENGTH} caracteres`);
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    throw new Error('A senha deve conter ao menos uma letra e um número');
  }
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
    const useMockData = !import.meta.env.PROD && import.meta.env.VITE_USE_MOCK_DATA === 'true';

    const restoreFromBackendToken = async (): Promise<boolean> => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      if (!accessToken) {
        return false;
      }

      const fetchMe = async (token: string) =>
        withTimeout(
          fetch(buildApiUrl('/api/v1/auth/me'), {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
          }),
          8000,
          'Timeout ao validar sessão'
        );

      try {
        let token = accessToken;
        let response = await fetchMe(token);

        if (response.status === 401 && refreshToken) {
          const refreshResponse = await withTimeout(
            fetch(buildApiUrl('/api/v1/auth/refresh'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken }),
            }),
            8000,
            'Timeout ao renovar sessão'
          );
          if (refreshResponse.ok) {
            const refreshed = await refreshResponse.json();
            token = refreshed.access_token;
            localStorage.setItem('access_token', refreshed.access_token);
            if (refreshed.refresh_token) {
              localStorage.setItem('refresh_token', refreshed.refresh_token);
            }
            response = await fetchMe(token);
          }
        }

        if (!response.ok) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          return false;
        }

        const me = (await response.json()) as BackendUserPayload;
        setUser(mapBackendUser(me));
        setSession({
          access_token: token,
          refresh_token: localStorage.getItem('refresh_token') || '',
        } as any);
        return true;
      } catch (restoreError) {
        console.warn('Falha ao validar sessão no backend:', restoreError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return false;
      }
    };

    const restoreSession = async () => {
      if (useMockData) {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        if (accessToken === 'mock-access-token' && refreshToken === 'mock-refresh-token') {
          setUser({
            id: 'mock-user-1',
            email: 'user@example.com',
            name: 'Mock User',
            company: 'Mock Company',
            role: 'user'
          });
          setSession({ access_token: accessToken, refresh_token: refreshToken } as any);
        }
        return;
      }

      await restoreFromBackendToken();
    };

    restoreSession().finally(() => setIsLoading(false));
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
          if (!data.user || !data.access_token) {
            throw new Error('Sessão inválida');
          }
          setUser(mapBackendUser(data.user));
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

        throw new Error('Falha de conexao com o servico de autenticacao. Verifique se a API esta online.');
      }
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
      assertPasswordPolicy(userData.password);

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
            if (!loginData.user || !loginData.access_token) {
              throw new Error('Cadastro realizado. Faca login para continuar.');
            }
            setUser(mapBackendUser(loginData.user));
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
        throw new Error('Falha de conexao com o servico de cadastro. Verifique se a API esta online.');
      }
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

    const SAFE_MSG = 'Se o e-mail estiver cadastrado, você receberá as instruções de recuperação.';
    // Redirect URL after password reset — must match an existing route
    const resetRedirectUrl = `${window.location.origin}/auth`;

    try {
      // 1. Try backend endpoint first
      const endpoint = buildApiUrl('/api/v1/auth/forgot-password');
      let backendSuccess = false;
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
          backendSuccess = true;
        }
        // Non-OK response: fall through to Supabase silently
      } catch (backendErr) {
        // Network error or timeout: fall through to Supabase silently
        console.warn('Backend forgot-password unavailable:', backendErr);
      }

      if (backendSuccess) {
        setSuccess(SAFE_MSG);
        return;
      }

      // 2. Fallback to Supabase directly
      const client = getSupabaseClient();
      if (client) {
        try {
          const { error } = await withTimeout(
            client.auth.resetPasswordForEmail(email, {
              redirectTo: resetRedirectUrl,
            }),
            10000,
            'Timeout ao solicitar recuperacao de senha'
          );
          if (error) {
            console.warn('Supabase resetPassword error:', error.message);
          }
        } catch (supabaseErr) {
          console.warn('Supabase fallback failed:', supabaseErr);
        }
      }

      // Always show safe success message regardless of outcome
      setSuccess(SAFE_MSG);
    } catch (err) {
      // Final safety net — show success message even on unexpected errors
      console.warn('resetPassword unexpected error:', err);
      setSuccess(SAFE_MSG);
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
