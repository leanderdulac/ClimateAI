import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import React from 'react';
import { vi } from 'vitest';

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
    onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    signInWithPassword: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
    resetPasswordForEmail: vi.fn(),
  },
  from: vi.fn().mockReturnThis(),
  select: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  single: vi.fn().mockResolvedValue({ data: null, error: null }),
  upsert: vi.fn().mockResolvedValue({ error: null }),
  update: vi.fn().mockResolvedValue({ error: null }),
};

vi.mock('./supabase', () => ({
  supabase: mockSupabase,
  isSupabaseConfigured: () => true,
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: { [key: string]: string } = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

const TestConsumer = () => {
  const { user, login, register, logout } = useAuth();
  return (
    <div>
      {user && <div data-testid="user-name">{user.name}</div>}
      <button onClick={() => register({ name: 'Test User', email: 'test@test.com', password: 'password' })}>Register</button>
      <button onClick={() => login('test@test.com', 'password')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('should allow a user to register and login', async () => {
    // Setup successful registration mock
    mockSupabase.auth.signUp.mockResolvedValueOnce({
      data: {
        user: { id: '123', email: 'test@test.com', user_metadata: { full_name: 'Test User' } },
        session: { user: { id: '123', email: 'test@test.com' } }
      },
      error: null
    });

    // Setup successful login mock
    mockSupabase.auth.signInWithPassword.mockResolvedValueOnce({
      data: {
        user: { id: '123', email: 'test@test.com', user_metadata: { full_name: 'Test User' } },
        session: { user: { id: '123', email: 'test@test.com' } }
      },
      error: null
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    // Register
    await act(async () => {
      screen.getByText('Register').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    }, { timeout: 2000 });

    // Logout
    await act(async () => {
      screen.getByText('Logout').click();
    });

    await waitFor(() => {
      expect(screen.queryByTestId('user-name')).not.toBeInTheDocument();
    });

    // Login
    await act(async () => {
      screen.getByText('Login').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    }, { timeout: 2000 });
  });
});
