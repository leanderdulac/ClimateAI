export function logError(error: Error, componentStack?: string) {
    console.error('Application Error:', {
        message: error.message,
        stack: error.stack,
        componentStack,
        timestamp: new Date().toISOString(),
    });
}

export function setupErrorHandlers() {
    window.onerror = function (msg, _url, _lineNo, _columnNo, error) {
        logError(error || new Error(String(msg)));
        return false;
    };

    window.addEventListener('unhandledrejection', function (event) {
        logError(event.reason);
    });
}