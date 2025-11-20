import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import {-after-|-before-|-context-|-case-sensitive-|-no-ignore-|-fixed-strings-|-include-|-before-|-after-|-context-|-case-sensitive-|-no-ignore-|-fixed-strings-|-include-} from 'react';

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
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    // Register
    await act(async () => {
      screen.getByText('Register').click();
    });

    // Logout
    await act(async () => {
      screen.getByText('Logout').click();
    });

    // Login
    await act(async () => {
      screen.getByText('Login').click();
    });

    expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
  });
});
