import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import React from 'react';
import { vi } from 'vitest';

// Mock global fetch so login() doesn't make real HTTP calls in CI
global.fetch = vi.fn().mockResolvedValue({
  ok: false,
  status: 503,
  json: async () => ({ detail: 'Service unavailable' }),
});

// Mock Supabase client
const { mockSupabase } = vi.hoisted(() => {
  const mock = {
    auth: {
      getSession: vi.fn(),
      onAuthStateChange: vi.fn(),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      resetPasswordForEmail: vi.fn(),
    },
    from: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    single: vi.fn(),
    upsert: vi.fn(),
    update: vi.fn(),
  };

  // Default implementations
  mock.auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
  mock.auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
  mock.auth.signInWithPassword.mockResolvedValue({ data: { user: null, session: null }, error: null });
  mock.auth.signUp.mockResolvedValue({ data: { user: null, session: null }, error: null });
  mock.auth.signOut.mockResolvedValue({ error: null });
  mock.from.mockReturnThis();
  mock.select.mockReturnThis();
  mock.eq.mockReturnThis();
  mock.single.mockResolvedValue({ data: { name: 'Test User', email: 'test@test.com' }, error: null });
  mock.upsert.mockResolvedValue({ error: null });
  mock.update.mockResolvedValue({ error: null });

  return { mockSupabase: mock };
});

vi.mock('./supabase', () => ({
  supabase: mockSupabase,
  getSupabaseClient: () => mockSupabase,
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
        session: { user: { id: '123', email: 'test@test.com' }, access_token: 'token-1', refresh_token: 'refresh-1' }
      },
      error: null
    });

    // Setup successful login mock
    mockSupabase.auth.signInWithPassword.mockResolvedValueOnce({
      data: {
        user: { id: '123', email: 'test@test.com', user_metadata: { full_name: 'Test User' } },
        session: { user: { id: '123', email: 'test@test.com' }, access_token: 'token-1', refresh_token: 'refresh-1' }
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

    // Note: register doesn't log the user in immediately, it shows a verification message.
    // So we don't expect the user to be set here.

    // Login
    await act(async () => {
      screen.getByText('Login').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    }, { timeout: 2000 });
  });
});
