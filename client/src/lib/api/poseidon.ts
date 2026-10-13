import { buildApiUrl } from './client';
import { getDefaultHeaders } from '../requestId';

export type PoseidonStatus = {
  ollama: boolean;
  host: string;
  model: string;
  model_present: boolean;
  models?: string[];
  error?: string;
};

export type PoseidonChatResult = {
  reply: string;
  model: string;
  tool_trace: Array<{
    tool: string;
    arguments: Record<string, unknown>;
    status?: string;
    source?: string;
  }>;
  rounds: number;
};

export type Envelope<T> = {
  data: T;
  meta: {
    live?: boolean;
    source?: string;
    status?: string;
    kind?: string;
    disclaimer?: string;
    [key: string]: unknown;
  };
};

export type CcoSystem = {
  id: string;
  name: string;
  kind: string;
  capacity_l_s: number;
  production_l_s: number;
  share_rm_pct?: number | null;
  population?: number;
  lat: number;
  lon: number;
  municipality?: string;
  notes?: string;
};

export type CcoConcessionaire = {
  id: string;
  name: string;
  blocks: string[];
  guandu_share: number;
  share_note?: string;
  municipalities: string[];
};

export type CcoDeliveryPoint = {
  id: string;
  name: string;
  kind: string;
  lat: number;
  lon: number;
  feeds?: string;
  concessionaire?: string;
};

export type CcoSystemsData = {
  systems: CcoSystem[];
  concessionaires: CcoConcessionaire[];
  delivery_points: CcoDeliveryPoint[];
  novo_guandu: Record<string, unknown>;
  share_assumption?: string;
};

export type CcoCma = {
  id: string;
  name: string;
  opened: string;
  lat: number;
  lon: number;
  cameras: number;
  points: number;
  status: string;
  notes?: string;
};

export type CcoConnector = {
  id: string;
  name: string;
  status: string;
  docs_url?: string;
  tool?: string;
  probe_status?: string;
};

export type CcoIncident = {
  id: string;
  kind: string;
  level: string;
  title: string;
  summary: string;
  playbook: string[];
  at: string;
  fixture?: boolean;
};

export type CcoPsa = {
  psa: {
    level: string;
    components: Record<string, string>;
    updated_at?: string;
    disclaimer?: string;
  };
  thresholds: Record<string, unknown>;
  last_geosmina?: {
    level: string;
    reasons?: string[];
    sop?: string[];
  } | null;
  sensor_online_geosmin_ngl?: boolean;
};

export type CcoDemanda = {
  horizonte_h: number;
  weather?: Record<string, unknown>;
  series: Array<{
    offset_h: number;
    at: string;
    local_hour: number;
    systems: Record<string, { point_l_s: number; low_l_s: number; high_l_s: number; capacity_l_s: number }>;
  }>;
  note?: string;
};

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') return body.detail;
  } catch {
    /* ignore */
  }
  return `Erro ${response.status}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: getDefaultHeaders(),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function getPoseidonStatus(): Promise<PoseidonStatus> {
  return requestJson<PoseidonStatus>('/api/v1/poseidon/status');
}

export async function chatPoseidon(
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
): Promise<PoseidonChatResult> {
  return requestJson<PoseidonChatResult>('/api/v1/poseidon/chat', {
    method: 'POST',
    body: JSON.stringify({ messages }),
  });
}

export async function getCcoSystems(): Promise<Envelope<CcoSystemsData>> {
  return requestJson('/api/v1/poseidon/cco/systems');
}

export async function getCcoCma(): Promise<Envelope<CcoCma>> {
  return requestJson('/api/v1/poseidon/cco/cma');
}

export async function getCcoConnectors(): Promise<Envelope<{ connectors: CcoConnector[] }>> {
  return requestJson('/api/v1/poseidon/cco/connectors');
}

export async function getCcoPsa(): Promise<Envelope<CcoPsa>> {
  return requestJson('/api/v1/poseidon/cco/psa');
}

export async function getCcoIncidents(): Promise<Envelope<{ incidents: CcoIncident[]; count: number }>> {
  return requestJson('/api/v1/poseidon/cco/incidents');
}

export async function postCcoDemoGeosmina(): Promise<Envelope<{ evaluation: { level: string; sop?: string[] }; incident: CcoIncident }>> {
  return requestJson('/api/v1/poseidon/cco/demo/geosmina', { method: 'POST' });
}

export async function postCcoDemoGuandu50(): Promise<Envelope<{ evaluation: { remaining_l_s: number; level: string }; incident: CcoIncident }>> {
  return requestJson('/api/v1/poseidon/cco/demo/guandu-50', { method: 'POST' });
}

export async function getCcoDemanda(horizonteH = 24): Promise<Envelope<CcoDemanda>> {
  return requestJson(`/api/v1/poseidon/cco/demanda?horizonte_h=${horizonteH}`);
}
