import { buildApiUrl } from './client';
import { fetchWithTracking } from '@/lib/requestId';

export type ProbeStatus = 'online' | 'offline' | 'session_expired';

export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch(buildApiUrl('/api/v1/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      return false;
    }
    const payload = (await response.json()) as {
      access_token?: string;
      refresh_token?: string;
    };
    if (!payload.access_token) {
      return false;
    }
    localStorage.setItem('access_token', payload.access_token);
    if (payload.refresh_token) {
      localStorage.setItem('refresh_token', payload.refresh_token);
    }
    return true;
  } catch {
    return false;
  }
}

export async function fetchWithAuthRetry(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  let response = await fetchWithTracking(input, init);
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetchWithTracking(input, init);
    }
  }
  return response;
}

export function classifyProbeStatus(response: Response | null | undefined): ProbeStatus {
  if (!response) {
    return 'offline';
  }
  if (response.status === 401) {
    return 'session_expired';
  }
  if (!response.ok) {
    return 'offline';
  }
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.toLowerCase().includes('application/json')) {
    return 'offline';
  }
  return 'online';
}

export function probeStatusLabel(
  status: ProbeStatus,
  t: (key: string) => string
): string {
  if (status === 'session_expired') {
    return t('atlas.status.sessionExpired');
  }
  if (status === 'online') {
    return t('atlas.status.online');
  }
  return t('atlas.status.offline');
}
