import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the App component', async () => {
    render(<App />);
    // You can add more specific assertions here if needed
    // For example, checking for a specific element that should be present
    await waitFor(() => {
      expect(screen.getByText(/ClimateAI/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
