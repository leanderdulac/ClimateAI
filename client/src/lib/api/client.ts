export function deriveApiBaseUrl(): string {
    const explicitBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
    if (explicitBaseUrl) {
        return explicitBaseUrl;
    }

    const legacyApiUrl = (import.meta.env.VITE_API_URL || '').trim();
    if (legacyApiUrl) {
        return legacyApiUrl.replace(/\/api\/v\d+(?:\/.*)?$/, '');
    }

    if (typeof window !== 'undefined') {
        const { hostname, protocol } = window.location;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `${protocol}//${hostname}:8000`;
        }
    }

    return '';
}

export function buildApiUrl(path: string): string {
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (useMockData) {
        return `/mock${path}`;
    }

    const baseUrl = deriveApiBaseUrl();

    if (!baseUrl) {
        return path.startsWith('/') ? path : `/${path}`;
    }

    const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${normalizedBaseUrl}${normalizedPath}`;
}
