import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/requestId', () => ({
  fetchWithTracking: vi.fn(),
}));

vi.mock('./client', () => ({
  buildApiUrl: (path: string) => `http://api.test${path}`,
}));

import { fetchWithTracking } from '@/lib/requestId';
import {
  classifyProbeStatus,
  fetchWithAuthRetry,
  probeStatusLabel,
  refreshAccessToken,
} from './authenticatedFetch';

const fetchWithTrackingMock = vi.mocked(fetchWithTracking);

function jsonResponse(status: number, body: unknown = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('classifyProbeStatus', () => {
  it('treats 401 as session expired, not offline', async () => {
    await expect(classifyProbeStatus(jsonResponse(200, { status: 'ok' }))).resolves.toBe(
      'online'
    );
    await expect(classifyProbeStatus(jsonResponse(401))).resolves.toBe('session_expired');
    await expect(classifyProbeStatus(jsonResponse(503))).resolves.toBe('offline');
    await expect(classifyProbeStatus(null)).resolves.toBe('offline');
  });

  it('treats HTML 200 (SPA fallback) as offline, not a live backend', async () => {
    const html = new Response('<!doctype html><html><body>ClimateWise</body></html>', {
      status: 200,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
    await expect(classifyProbeStatus(html)).resolves.toBe('offline');
  });

  it('treats 200 with HTML body labeled as JSON as offline', async () => {
    const spoofed = new Response('<!doctype html><html><body>ClimateWise</body></html>', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    await expect(classifyProbeStatus(spoofed)).resolves.toBe('offline');
  });

  it('requires a string status field when asked (Backend API health)', async () => {
    await expect(
      classifyProbeStatus(jsonResponse(200, { ok: true }), { requireStatusField: true })
    ).resolves.toBe('offline');
    await expect(
      classifyProbeStatus(jsonResponse(200, { status: 'healthy' }), {
        requireStatusField: true,
      })
    ).resolves.toBe('online');
  });
});

describe('probeStatusLabel', () => {
  const t = (key: string) =>
    ({
      'atlas.status.sessionExpired': 'sessão expirada',
      'atlas.status.online': 'online',
      'atlas.status.offline': 'offline',
    })[key] || key;

  it('labels 401 as sessão expirada', () => {
    expect(probeStatusLabel('session_expired', t)).toBe('sessão expirada');
    expect(probeStatusLabel('offline', t)).toBe('offline');
  });
});

describe('refreshAccessToken', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('returns false without a refresh token', async () => {
    await expect(refreshAccessToken()).resolves.toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('stores rotated tokens on success', async () => {
    localStorage.setItem('refresh_token', 'old-refresh');
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse(200, { access_token: 'new-access', refresh_token: 'new-refresh' })
    );

    await expect(refreshAccessToken()).resolves.toBe(true);
    expect(localStorage.getItem('access_token')).toBe('new-access');
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh');
    expect(fetch).toHaveBeenCalledWith(
      'http://api.test/api/v1/auth/refresh',
      expect.objectContaining({ method: 'POST' })
    );
  });
});

describe('fetchWithAuthRetry', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal('fetch', vi.fn());
    fetchWithTrackingMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('retries once after a successful token refresh', async () => {
    localStorage.setItem('refresh_token', 'refresh-1');
    fetchWithTrackingMock
      .mockResolvedValueOnce(jsonResponse(401))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { access_token: 'rotated' }));

    const response = await fetchWithAuthRetry('http://api.test/api/v1/atlas-simulation/oracle-status');
    expect(response.ok).toBe(true);
    expect(fetchWithTrackingMock).toHaveBeenCalledTimes(2);
    expect(localStorage.getItem('access_token')).toBe('rotated');
  });

  it('keeps 401 so callers can show sessão expirada', async () => {
    fetchWithTrackingMock.mockResolvedValue(jsonResponse(401));
    const response = await fetchWithAuthRetry('http://api.test/api/v1/celestrak/space-weather');
    expect(response.status).toBe(401);
    await expect(classifyProbeStatus(response)).resolves.toBe('session_expired');
    expect(fetchWithTrackingMock).toHaveBeenCalledTimes(1);
  });
});
