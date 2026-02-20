import { AppRoutes } from './routes';
import { AuthProvider } from './lib/AuthContext';
import { LocationProvider } from './lib/LocationContext';
import { PeriodProvider } from './lib/PeriodContext';
import { ClimateAssistant } from './components/ClimateAssistant';
import { useConsent, ConsentBanner } from './hooks/useConsent';

export default function App() {
  const { showBanner, acceptAll, acceptNecessary, customizeConsent } = useConsent();

  return (
    <AuthProvider>
      <LocationProvider>
        <PeriodProvider>
          <div className="app">
            <AppRoutes />
            <ClimateAssistant />
            <ConsentBanner
              show={showBanner}
              onAcceptAll={acceptAll}
              onAcceptNecessary={acceptNecessary}
              onCustomize={customizeConsent}
              onClose={() => {}}
            />
          </div>
        </PeriodProvider>
      </LocationProvider>
    </AuthProvider>
  );
}
