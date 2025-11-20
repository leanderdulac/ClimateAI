import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { setupErrorHandlers, logError } from '@/lib/error-handler'
import { LanguageProvider } from './contexts/LanguageContext';

// Setup global error handlers
setupErrorHandlers();

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean, error: Error | null }
> {
// ... (rest of the file is the same)
// ...
ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary>
      <LanguageProvider>
        <App />
      </LanguageProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
