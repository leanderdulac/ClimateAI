import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./authenticatedFetch', async () => {
  const actual = await vi.importActual<typeof import('./authenticatedFetch')>(
    './authenticatedFetch'
  );
  return {
    ...actual,
    fetchWithAuthRetry: vi.fn(),
  };
});

vi.mock('./client', () => ({
  buildApiUrl: (path: string) => path,
}));

import { fetchWithAuthRetry } from './authenticatedFetch';
import {
  badgeTone,
  baseBadgeLabel,
  baseBlockLabel,
  contractBadgeLabel,
  fetchBaseL2Status,
  fetchOracleCommandStatus,
  oracleBadgeLabel,
  oracleConsensusLabel,
  policyExplorerUrl,
  shortenAddress,
} from './baseL2Status';

const fetchWithAuthRetryMock = vi.mocked(fetchWithAuthRetry);

function jsonResponse(status: number, body: unknown = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const t = (key: string, vars?: Record<string, unknown>) => {
  const table: Record<string, string> = {
    'compute.status.checking': 'Verificando…',
    'compute.unavailable': 'indisponível',
    'atlas.status.sessionExpired': 'sessão expirada',
    'compute.base.block': `Bloco ${vars?.block}`,
    'compute.base.blockUnavailable': 'Bloco —',
    'compute.base.status.online': 'online',
    'compute.base.status.offline': 'offline',
    'compute.base.status.notConfigured': 'não configurado',
    'compute.oracle.subtitle': 'Consenso 2-de-3',
    'compute.oracle.consensusLine': `${vars?.status} · 2-de-3 · ${vars?.events} eventos`,
  };
  return table[key] || key;
};

describe('shortenAddress / policyExplorerUrl', () => {
  it('shortens a policy address', () => {
    expect(shortenAddress('0xabcdef0123456789abcdef')).toBe('0xabcd…cdef');
  });

  it('builds explorer_url/address/<addr> and strips trailing slash', () => {
    expect(policyExplorerUrl('https://sepolia.basescan.org/', '0xabc')).toBe(
      'https://sepolia.basescan.org/address/0xabc'
    );
  });
});

describe('command-center labels', () => {
  it('shows latest_block and badge from Base status', () => {
    const online = {
      ok: true as const,
      data: {
        status: 'online' as const,
        latest_block: 16,
        contracts: { policy: '0xabc' },
      },
    };
    expect(baseBlockLabel(online, t)).toBe('Bloco 16');
    expect(baseBadgeLabel(online, t)).toBe('online');
    expect(baseBadgeLabel({ ok: true, data: { status: 'not_configured' } }, t)).toBe(
      'não configurado'
    );
    expect(baseBadgeLabel({ ok: true, data: { status: 'offline' } }, t)).toBe('offline');
  });

  it('shows sessão expirada after a 401', () => {
    const expired = { ok: false as const, reason: 'session_expired' as const };
    expect(baseBadgeLabel(expired, t)).toBe('sessão expirada');
    expect(oracleBadgeLabel(expired, t)).toBe('sessão expirada');
    expect(contractBadgeLabel(expired, t)).toBe('sessão expirada');
  });

  it('shows oracle status and consensus counts', () => {
    const oracle = {
      ok: true as const,
      data: { status: 'healthy', total_events_processed: 12 },
    };
    expect(oracleConsensusLabel(oracle, t)).toBe('healthy · 2-de-3 · 12 eventos');
    expect(oracleBadgeLabel(oracle, t)).toBe('healthy');
    expect(badgeTone(oracle)).toBe('online');
  });

  it('greens the contract badge when Base is online', () => {
    expect(badgeTone({ ok: true, data: { status: 'online' } })).toBe('online');
    expect(badgeTone({ ok: true, data: { status: 'not_configured' } })).toBe('muted');
  });
});

describe('fetchBaseL2Status / fetchOracleCommandStatus', () => {
  beforeEach(() => {
    fetchWithAuthRetryMock.mockReset();
  });

  afterEach(() => {
    fetchWithAuthRetryMock.mockReset();
  });

  it('parses Base L2 status over fetchWithAuthRetry', async () => {
    fetchWithAuthRetryMock.mockResolvedValue(
      jsonResponse(200, {
        status: 'online',
        latest_block: 99,
        explorer_url: 'https://sepolia.basescan.org',
        contracts: { policy: '0xpolicy' },
      })
    );
    await expect(fetchBaseL2Status()).resolves.toEqual({
      ok: true,
      data: {
        status: 'online',
        latest_block: 99,
        explorer_url: 'https://sepolia.basescan.org',
        contracts: { policy: '0xpolicy' },
      },
    });
    expect(fetchWithAuthRetryMock).toHaveBeenCalledWith('/api/v1/blockchain/base/status');
  });

  it('maps 401 after refresh to session_expired', async () => {
    fetchWithAuthRetryMock.mockResolvedValue(jsonResponse(401, { detail: 'Não autenticado' }));
    await expect(fetchOracleCommandStatus()).resolves.toEqual({
      ok: false,
      reason: 'session_expired',
    });
    expect(fetchWithAuthRetryMock).toHaveBeenCalledWith(
      '/api/v1/atlas-simulation/oracle-status'
    );
  });

  it('maps non-401 failures to unavailable', async () => {
    fetchWithAuthRetryMock.mockResolvedValue(jsonResponse(503, { detail: 'down' }));
    await expect(fetchBaseL2Status()).resolves.toEqual({
      ok: false,
      reason: 'unavailable',
    });
  });
});
