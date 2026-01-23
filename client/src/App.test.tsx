import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { LocationProvider } from './lib/LocationContext';
import { LanguageProvider } from './contexts/LanguageContext';

describe('App', () => {
  it('renders the App component', async () => {
    render(
      <LanguageProvider>
        <LocationProvider>
          <App />
        </LocationProvider>
      </LanguageProvider>
    );
    // Find and click the assistant button
    await waitFor(() => {
      screen.getByTestId('climate-assistant-trigger').click();
    });

    // Now the title should be visible
    await waitFor(() => {
      expect(screen.getByText(/Climate Assistant/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
