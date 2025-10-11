import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { setupErrorHandlers, logError } from './lib/error-handler'

// Setup global error handlers
setupErrorHandlers();

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean, error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logError(error, errorInfo.componentStack || '');
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-white p-4">
          <div className="container mx-auto max-w-4xl">
            <div className="p-6 bg-red-50 border border-red-200 rounded-xl shadow-sm">
              <h1 className="text-2xl font-bold text-red-700 mb-4">Something went wrong</h1>
              <div className="bg-white p-4 rounded-lg border border-red-100">
                <pre className="text-sm text-red-600 whitespace-pre-wrap overflow-auto">
                  {this.state.error?.message}
                </pre>
              </div>
              <div className="mt-6 flex gap-4">
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Reload Page
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                >
                  Go to Homepage
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const root = document.getElementById('root');

if (!root) {
  throw new Error('Root element not found. Make sure there is a <div id="root"></div> in your HTML');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
