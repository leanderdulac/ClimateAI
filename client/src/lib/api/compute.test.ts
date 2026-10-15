import { describe, expect, it } from 'vitest';

import { computeStatusLabel, type ComputeStatus } from './compute';

const t = (key: string, vars?: Record<string, string | number>) => {
  if (key === 'compute.status.online') return `Online • ${vars?.ms}ms`;
  if (key === 'compute.status.offline') return 'Offline — cálculo local';
  if (key === 'compute.status.notConfigured') return 'Não configurado — cálculo local';
  if (key === 'compute.status.checking') return 'Verificando…';
  return key;
};

describe('computeStatusLabel', () => {
  it('formats online latency', () => {
    const status: ComputeStatus = {
      status: 'online',
      mode: 'remote',
      latency_ms: 38.4,
      last_checked: '2026-10-14T00:00:00Z',
    };
    expect(computeStatusLabel(status, t)).toBe('Online • 38ms');
  });

  it('formats offline and not configured', () => {
    expect(
      computeStatusLabel(
        { status: 'offline', mode: 'local_fallback', latency_ms: 2500, last_checked: null },
        t
      )
    ).toBe('Offline — cálculo local');
    expect(
      computeStatusLabel(
        { status: 'not_configured', mode: 'local', latency_ms: null, last_checked: null },
        t
      )
    ).toBe('Não configurado — cálculo local');
  });

  it('shows checking when status is missing', () => {
    expect(computeStatusLabel(null, t)).toBe('Verificando…');
  });
});
