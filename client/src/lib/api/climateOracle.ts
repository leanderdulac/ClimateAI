import { buildApiUrl } from './client';
import { fetchWithTracking } from '@/lib/requestId';

export interface ClimateIndexRequest {
  index_type: string;
  latitude: number;
  longitude: number;
  start_date: string;
  end_date: string;
  trigger_value: number;
  trigger_condition: 'above' | 'below';
  source?: string;
}

export interface ClimateIndexResponse {
  index_type: string;
  region: string;
  latitude: number;
  longitude: number;
  start_date: string;
  end_date: string;
  index_value: number;
  trigger_value: number;
  trigger_condition: string;
  trigger_met: boolean;
  data_points_count: number;
  calculation_method: string;
}

export async function getClimateIndex(
  data: ClimateIndexRequest
): Promise<ClimateIndexResponse> {
  const response = await fetchWithTracking(buildApiUrl('/api/v1/oracle/index'), {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `oracle index ${response.status}`);
  }
  return response.json();
}
