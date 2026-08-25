import { buildApiUrl } from './client';
import { getDefaultHeaders } from '../requestId';

export type Partner = {
  id: string;
  name: string;
  slug: string;
  contact_email: string | null;
  api_enabled: boolean;
  created_at: string;
};

export type PartnerApiKey = {
  id: string;
  prefix: string;
  name: string | null;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
};

export type CreatedPartnerApiKey = PartnerApiKey & {
  secret_key: string;
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') {
      return body.detail;
    }
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg;
    }
  } catch {
    /* ignore */
  }
  return `Erro ${response.status}`;
}

export async function listPartners(): Promise<Partner[]> {
  const response = await fetch(buildApiUrl('/api/v1/partners'), { headers: getDefaultHeaders() });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function createPartner(payload: {
  name: string;
  slug?: string;
  contact_email?: string;
}): Promise<Partner> {
  const response = await fetch(buildApiUrl('/api/v1/partners'), {
    method: 'POST',
    headers: getDefaultHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function updatePartner(
  partnerId: string,
  payload: { api_enabled?: boolean }
): Promise<Partner> {
  const response = await fetch(buildApiUrl(`/api/v1/partners/${partnerId}`), {
    method: 'PATCH',
    headers: getDefaultHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function listPartnerKeys(partnerId: string): Promise<PartnerApiKey[]> {
  const response = await fetch(buildApiUrl(`/api/v1/partners/${partnerId}/api-keys`), {
    headers: getDefaultHeaders(),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function generatePartnerKey(
  partnerId: string,
  name: string
): Promise<CreatedPartnerApiKey> {
  const response = await fetch(buildApiUrl(`/api/v1/partners/${partnerId}/api-keys`), {
    method: 'POST',
    headers: getDefaultHeaders(),
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function revokePartnerKey(partnerId: string, keyId: string): Promise<void> {
  const response = await fetch(buildApiUrl(`/api/v1/partners/${partnerId}/api-keys/${keyId}`), {
    method: 'DELETE',
    headers: getDefaultHeaders(),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}
