import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./authenticatedFetch', async () => {
  const actual = await vi.importActual<typeof import('./authenticatedFetch')>('./authenticatedFetch');
  return {
    ...actual,
    fetchWithAuthRetry: vi.fn(),
  };
});

vi.mock('./client', () => ({
  buildApiUrl: (path: string) => path,
}));

import { ATLAS_STATUS_ENDPOINTS, fetchAtlasDashboard, refreshNewsAlerts } from './atlas';
import { fetchWithAuthRetry } from './authenticatedFetch';

const fetchWithAuthRetryMock = vi.mocked(fetchWithAuthRetry);

function jsonResponse(status: number, body: unknown = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('ATLAS_STATUS_ENDPOINTS', () => {
  it('probes dedicated services instead of portfolio-risk', () => {
    expect(ATLAS_STATUS_ENDPOINTS.backend).toBe('/health');
    expect(ATLAS_STATUS_ENDPOINTS.oracle).toBe('/api/v1/atlas-simulation/oracle-status');
    expect(ATLAS_STATUS_ENDPOINTS.blockchain).toBe('/api/v1/blockchain/hathor/status');
    expect(ATLAS_STATUS_ENDPOINTS.weather).toBe('/api/v1/atlas-realtime/health');
    expect(ATLAS_STATUS_ENDPOINTS.celestrak).toBe('/api/v1/celestrak/space-weather');
    expect(Object.values(ATLAS_STATUS_ENDPOINTS)).not.toContain(
      '/api/v1/atlas-simulation/portfolio-risk'
    );
  });
});

describe('fetchAtlasDashboard', () => {
  beforeEach(() => {
    fetchWithAuthRetryMock.mockReset();
  });

  afterEach(() => {
    fetchWithAuthRetryMock.mockReset();
  });

  it('classifies 401 probes as session_expired and still loads payload data', async () => {
    fetchWithAuthRetryMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url === '/health') return jsonResponse(200, { status: 'ok' });
      if (url === '/api/v1/atlas-simulation/oracle-status') {
        return jsonResponse(401, { detail: 'Não autenticado' });
      }
      if (url === '/api/v1/blockchain/hathor/status') return jsonResponse(200, { network: 'testnet' });
      if (url === '/api/v1/atlas-realtime/health') return jsonResponse(200, { status: 'healthy' });
      if (url === '/api/v1/celestrak/space-weather') return jsonResponse(503, { detail: 'down' });
      if (url === '/api/v1/atlas-simulation/portfolio-risk') {
        return jsonResponse(200, { summary: { total_exposure: 10, total_alerts: 2 } });
      }
      if (url.startsWith('/api/v1/atlas-simulation/live-events')) {
        return jsonResponse(200, [{ disaster_type: 'seca', severity_score: 3 }]);
      }
      if (url === '/api/v1/atlas-realtime/all-cities') {
        return jsonResponse(200, { data: [{ city: 'SP' }] });
      }
      return jsonResponse(200, {});
    });

    const dashboard = await fetchAtlasDashboard();
    expect(dashboard.connections.backend).toBe('online');
    expect(dashboard.connections.oracle).toBe('session_expired');
    expect(dashboard.connections.blockchain).toBe('online');
    expect(dashboard.connections.weather).toBe('online');
    expect(dashboard.connections.celestrak).toBe('offline');
    expect(dashboard.portfolioRisk.summary?.total_exposure).toBe(10);
    expect(dashboard.liveEvents).toHaveLength(1);
    expect(dashboard.realtimeWeather[0]?.city).toBe('SP');
  });
});

describe('refreshNewsAlerts', () => {
  beforeEach(() => {
    fetchWithAuthRetryMock.mockReset();
  });

  it('uses authenticated refresh + alerts endpoints', async () => {
    fetchWithAuthRetryMock
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          alerts: [{ alert_id: 'n1', title: 'Chuva', locations: [], confidence: 0.8 }],
        })
      );

    const alerts = await refreshNewsAlerts();
    expect(alerts[0]?.alert_id).toBe('n1');
    expect(fetchWithAuthRetryMock).toHaveBeenNthCalledWith(
      1,
      '/api/v1/news-crawler/refresh',
      { method: 'POST' }
    );
    expect(fetchWithAuthRetryMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/news-crawler/alerts?limit=20'
    );
  });
});
