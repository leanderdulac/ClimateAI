import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import React from 'react';
import { vi } from 'vitest';

// Mock global fetch to simulate network failure so AuthContext falls back to Supabase
global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

// Mock Supabase client
const { mockSupabase } = vi.hoisted(() => {
  const singleMock = vi.fn().mockResolvedValue({
    data: { full_name: 'Test User', email: 'test@test.com', company_name: '', avatar_url: '', role: 'user' },
    error: null
  });
  const eqMock = vi.fn().mockReturnValue({ single: singleMock });
  const selectMock = vi.fn().mockReturnValue({ eq: eqMock });
  const fromMock = vi.fn().mockReturnValue({ select: selectMock, eq: eqMock, single: singleMock });

  const mock = {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
      signInWithPassword: vi.fn().mockResolvedValue({ data: { user: null, session: null }, error: null }),
      signUp: vi.fn().mockResolvedValue({ data: { user: null, session: null }, error: null }),
      signOut: vi.fn().mockResolvedValue({ error: null }),
      resetPasswordForEmail: vi.fn().mockResolvedValue({ error: null }),
    },
    from: fromMock,
    select: selectMock,
    eq: eqMock,
    single: singleMock,
  };

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
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
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
    vi.clearAllMocks();
    // Re-apply default mocks after clearAllMocks
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    mockSupabase.auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
    mockSupabase.auth.signInWithPassword.mockResolvedValue({ data: { user: null, session: null }, error: null });
    mockSupabase.auth.signUp.mockResolvedValue({ data: { user: null, session: null }, error: null });
    mockSupabase.auth.signOut.mockResolvedValue({ error: null });
  });

  it('should allow a user to register and login via Supabase fallback', async () => {
    const mockUser = { id: '123', email: 'test@test.com', user_metadata: { full_name: 'Test User' } };
    const mockSession = {
      user: mockUser,
      access_token: 'token-1',
      refresh_token: 'refresh-1'
    };

    // Supabase signUp succeeds
    mockSupabase.auth.signUp.mockResolvedValueOnce({
      data: { user: mockUser, session: mockSession },
      error: null
    });

    // Supabase signInWithPassword succeeds
    mockSupabase.auth.signInWithPassword.mockResolvedValueOnce({
      data: { user: mockUser, session: mockSession },
      error: null
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    // Register — fetch throws network error → falls back to Supabase signUp → sets user via session
    await act(async () => {
      try { screen.getByText('Register').click(); } catch { /* expected: register re-throws */ }
    });

    // Login — fetch throws network error → falls back to Supabase signInWithPassword → sets user
    await act(async () => {
      try { screen.getByText('Login').click(); } catch { /* expected: login re-throws */ }
    });

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    }, { timeout: 3000 });
  });
});
