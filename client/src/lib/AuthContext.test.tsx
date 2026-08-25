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
      <button onClick={() => register({ name: 'Test User', email: 'test@test.com', password: 'password123' })}>Register</button>
      <button onClick={() => login('test@test.com', 'password123')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
    vi.mocked(global.fetch).mockRejectedValue(new TypeError('Failed to fetch'));
    // Re-apply default mocks after clearAllMocks
    mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    mockSupabase.auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
    mockSupabase.auth.signInWithPassword.mockResolvedValue({ data: { user: null, session: null }, error: null });
    mockSupabase.auth.signUp.mockResolvedValue({ data: { user: null, session: null }, error: null });
    mockSupabase.auth.signOut.mockResolvedValue({ error: null });
  });

  it('logs in via backend JWT and does not use Supabase session', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        user: { id: '123', email: 'test@test.com', full_name: 'Test User', role: 'user' },
        access_token: 'jwt-access',
        refresh_token: 'jwt-refresh',
      }),
    } as Response);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText('Login').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });
    expect(mockSupabase.auth.signInWithPassword).not.toHaveBeenCalled();
    expect(window.localStorage.getItem('access_token')).toBe('jwt-access');
  });

  it('does not treat arbitrary localStorage tokens as a logged-in user', async () => {
    window.localStorage.setItem('access_token', 'forged-token');
    window.localStorage.setItem('refresh_token', 'forged-refresh');

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('user-name')).not.toBeInTheDocument();
    });
    expect(window.localStorage.getItem('access_token')).toBeNull();
  });
});
