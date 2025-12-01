import { AppRoutes } from './routes';
import { AuthProvider } from './lib/AuthContext';
import { ClimateAssistant } from './components/ClimateAssistant';

export default function App() {
  return (
    <AuthProvider>
      <div className="app">
        <AppRoutes />
        <ClimateAssistant />
      </div>
    </AuthProvider>
  );
}
