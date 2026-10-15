import { buildApiUrl } from './client';
import { fetchWithTracking } from '@/lib/requestId';

export type ComputeStatusValue = 'online' | 'offline' | 'not_configured';
export type ComputeMode = 'remote' | 'local' | 'local_fallback';

export interface ComputeStatus {
  status: ComputeStatusValue;
  mode: ComputeMode;
  latency_ms: number | null;
  last_checked: string | null;
}

export function computeStatusLabel(
  status: ComputeStatus | null,
  t: (key: string, params?: Record<string, unknown>) => string
): string {
  if (!status) {
    return t('compute.status.checking');
  }
  if (status.status === 'online' && status.latency_ms != null) {
    return t('compute.status.online', { ms: Math.round(status.latency_ms) });
  }
  if (status.status === 'offline') {
    return t('compute.status.offline');
  }
  if (status.status === 'not_configured') {
    return t('compute.status.notConfigured');
  }
  return t('compute.status.checking');
}

export const computeApi = {
  async getStatus(): Promise<ComputeStatus> {
    const response = await fetchWithTracking(buildApiUrl('/api/v1/compute/status'));
    if (!response.ok) {
      throw new Error(`compute status ${response.status}`);
    }
    return response.json();
  },
};
