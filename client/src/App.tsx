import { AppRoutes } from './routes';
import { AuthProvider } from './lib/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';

export default function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <div className="app">
          <AppRoutes />
        </div>
      </LanguageProvider>
    </AuthProvider>
  );
}
