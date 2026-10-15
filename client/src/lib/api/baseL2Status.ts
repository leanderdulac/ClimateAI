import { buildApiUrl } from './client';
import { fetchWithAuthRetry } from './authenticatedFetch';

export type BaseL2ProbeStatus = 'online' | 'offline' | 'not_configured';

export interface BaseL2Status {
  status: BaseL2ProbeStatus;
  network?: string;
  chain_id?: number | null;
  latest_block?: number | null;
  explorer_url?: string | null;
  contracts?: {
    policy?: string | null;
    operator?: string | null;
  };
  last_checked?: string | null;
}

export interface OracleCommandStatus {
  status?: string;
  mode?: string;
  total_events_processed?: number;
  total_payouts_triggered?: number;
  network?: string;
}

export type AuthStatusResult<T> =
  | { ok: true; data: T }
  | { ok: false; reason: 'session_expired' | 'unavailable' };

async function readAuthJson<T>(path: string): Promise<AuthStatusResult<T>> {
  try {
    const response = await fetchWithAuthRetry(buildApiUrl(path));
    if (response.status === 401) {
      return { ok: false, reason: 'session_expired' };
    }
    if (!response.ok) {
      return { ok: false, reason: 'unavailable' };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, reason: 'unavailable' };
  }
}

export function fetchBaseL2Status(): Promise<AuthStatusResult<BaseL2Status>> {
  return readAuthJson<BaseL2Status>('/api/v1/blockchain/base/status');
}

export function fetchOracleCommandStatus(): Promise<AuthStatusResult<OracleCommandStatus>> {
  return readAuthJson<OracleCommandStatus>('/api/v1/atlas-simulation/oracle-status');
}

export function shortenAddress(address: string): string {
  const trimmed = address.trim();
  if (trimmed.length <= 12) {
    return trimmed;
  }
  return `${trimmed.slice(0, 6)}…${trimmed.slice(-4)}`;
}

export function policyExplorerUrl(
  explorerUrl: string | null | undefined,
  address: string
): string {
  const base = (explorerUrl || 'https://sepolia.basescan.org').replace(/\/+$/, '');
  return `${base}/address/${address}`;
}

type Translate = (key: string, params?: Record<string, unknown>) => string;

function failureLabel(
  result: AuthStatusResult<unknown> | null,
  t: Translate
): string | null {
  if (!result) {
    return t('compute.status.checking');
  }
  if (result.ok) {
    return null;
  }
  if (result.reason === 'session_expired') {
    return t('atlas.status.sessionExpired');
  }
  return t('compute.unavailable');
}

export function baseBlockLabel(
  result: AuthStatusResult<BaseL2Status> | null,
  t: Translate
): string {
  if (result?.ok && result.data.latest_block != null) {
    return t('compute.base.block', { block: result.data.latest_block });
  }
  return t('compute.base.blockUnavailable');
}

export function baseBadgeLabel(
  result: AuthStatusResult<BaseL2Status> | null,
  t: Translate
): string {
  const failed = failureLabel(result, t);
  if (failed) {
    return failed;
  }
  const status = result && result.ok ? result.data.status : undefined;
  if (status === 'online') {
    return t('compute.base.status.online');
  }
  if (status === 'not_configured') {
    return t('compute.base.status.notConfigured');
  }
  if (status === 'offline') {
    return t('compute.base.status.offline');
  }
  return t('compute.unavailable');
}

export function oracleConsensusLabel(
  result: AuthStatusResult<OracleCommandStatus> | null,
  t: Translate
): string {
  if (result?.ok) {
    return t('compute.oracle.consensusLine', {
      status: result.data.status || t('compute.oracle.subtitle'),
      events: result.data.total_events_processed ?? 0,
    });
  }
  return t('compute.oracle.subtitle');
}

export function oracleBadgeLabel(
  result: AuthStatusResult<OracleCommandStatus> | null,
  t: Translate
): string {
  const failed = failureLabel(result, t);
  if (failed) {
    return failed;
  }
  return result && result.ok && result.data.status
    ? result.data.status
    : t('compute.unavailable');
}

export function contractBadgeLabel(
  result: AuthStatusResult<BaseL2Status> | null,
  t: Translate
): string {
  return baseBadgeLabel(result, t);
}

export function badgeTone(
  result: AuthStatusResult<{ status?: string }> | null
): 'online' | 'offline' | 'expired' | 'muted' {
  if (!result) {
    return 'muted';
  }
  if (!result.ok) {
    return result.reason === 'session_expired' ? 'expired' : 'muted';
  }
  const status = result.data.status;
  if (status === 'online' || status === 'healthy') {
    return 'online';
  }
  if (status === 'offline') {
    return 'offline';
  }
  return 'muted';
}
