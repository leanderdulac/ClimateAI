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
    await waitFor(() => {
      expect(screen.getByTestId('climate-assistant-trigger')).toBeInTheDocument();
    }, { timeout: 10000 });
  });
});
