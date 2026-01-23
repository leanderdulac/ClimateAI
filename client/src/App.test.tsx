import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

import { MemoryRouter } from 'react-router-dom';

describe('App', () => {
  it('renders the App component', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    // You can add more specific assertions here if needed
    // For example, checking for a specific element that should be present
    await waitFor(() => {
      expect(screen.getByText(/ClimateAI/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
