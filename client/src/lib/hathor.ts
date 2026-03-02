/**
 * Hathor Blockchain API Client
 * 
 * Integração com a API Hathor Blockchain para tokenização de índices climáticos.
 * 
 * Endpoints:
 * - POST /tokens/create - Criar token climático
 * - POST /tokens/transfer - Transferir tokens
 * - POST /tokens/{uid}/payout - Executar payout
 * - GET /tokens - Listar tokens
 * - POST /oracle/index - Obter índice climático
 */

import axios from 'axios';
import { buildApiUrl } from './api';

// API base URL (ajustar para produção)
const HATHOR_API_BASE = import.meta.env.VITE_HATHOR_API_URL || buildApiUrl('/api/v1/blockchain/hathor');

// Create axios instance
export const hathorApi = axios.create({
  baseURL: HATHOR_API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface ClimateTokenMetadata {
  index_type: 'drought' | 'flood' | 'temperature' | 'precipitation' | 'wind' | 'hurricane' | 'frost' | 'heatwave';
  region: string;
  latitude: number;
  longitude: number;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  trigger_value: number;
  trigger_condition: 'above' | 'below';
  payout_amount: number;
  currency: string;
  oracle_source: string;
}

export interface CreateTokenRequest {
  name: string;
  symbol: string;
  total_supply: number;
  index_type: ClimateTokenMetadata['index_type'];
  region: string;
  latitude: number;
  longitude: number;
  start_date: string;
  end_date: string;
  trigger_value: number;
  trigger_condition: 'above' | 'below';
  payout_amount: number;
  currency: string;
  oracle_source: string;
}

export interface CreateTokenResponse {
  success: boolean;
  token_uid: string;
  name: string;
  symbol: string;
  total_supply: number;
  tx_hash: string;
  explorer_url: string;
  message: string;
}

export interface TransferTokenRequest {
  token_uid: string;
  amount: number;
  destination_address: string;
  message?: string;
}

export interface TransferTokenResponse {
  success: boolean;
  tx_hash: string;
  token_uid: string;
  amount: number;
  destination_address: string;
  explorer_url: string;
  message: string;
}

export interface ExecutePayoutRequest {
  beneficiary_address: string;
  oracle_value?: number;
}

export interface ExecutePayoutResponse {
  success: boolean;
  tx_hash: string;
  token_uid: string;
  payout_amount: number;
  beneficiary_address: string;
  oracle_value: number;
  trigger_value: number;
  trigger_met: boolean;
  explorer_url: string;
  message: string;
}

export interface TokenInfo {
  token_uid: string;
  name: string;
  symbol: string;
  status: 'active' | 'triggered' | 'paid_out' | 'expired' | 'cancelled';
  total_supply: number;
  index_type: string;
  region: string;
  trigger_value: number;
  trigger_condition: string;
  payout_amount: number;
  payout_executed: boolean;
  created_at: string;
}

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

export interface WalletBalanceResponse {
  token_uid: string;
  available: number;
  locked: number;
  total: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Create a new climate token
 */
export const createClimateToken = async (data: CreateTokenRequest): Promise<CreateTokenResponse> => {
  try {
    const response = await hathorApi.post<CreateTokenResponse>('/tokens/create', data);
    return response.data;
  } catch (error) {
    console.error('Error creating climate token:', error);
    throw error;
  }
};

/**
 * Create a drought index token (convenience method)
 */
export const createDroughtToken = async (
  region: string,
  latitude: number,
  longitude: number,
  start_date: string,
  end_date: string,
  trigger_precipitation_mm: number,
  payout_amount: number,
  total_supply: number = 10000
): Promise<CreateTokenResponse> => {
  const response = await hathorApi.post<CreateTokenResponse>(
    '/tokens/create/drought',
    null,
    {
      params: {
        region,
        latitude,
        longitude,
        start_date,
        end_date,
        trigger_precipitation_mm,
        payout_amount,
        total_supply,
      },
    }
  );
  return response.data;
};

/**
 * Create a flood index token (convenience method)
 */
export const createFloodToken = async (
  region: string,
  latitude: number,
  longitude: number,
  start_date: string,
  end_date: string,
  trigger_precipitation_mm: number,
  payout_amount: number,
  total_supply: number = 10000
): Promise<CreateTokenResponse> => {
  const response = await hathorApi.post<CreateTokenResponse>(
    '/tokens/create/flood',
    null,
    {
      params: {
        region,
        latitude,
        longitude,
        start_date,
        end_date,
        trigger_precipitation_mm,
        payout_amount,
        total_supply,
      },
    }
  );
  return response.data;
};

/**
 * Transfer tokens to another address
 */
export const transferTokens = async (data: TransferTokenRequest): Promise<TransferTokenResponse> => {
  try {
    const response = await hathorApi.post<TransferTokenResponse>('/tokens/transfer', data);
    return response.data;
  } catch (error) {
    console.error('Error transferring tokens:', error);
    throw error;
  }
};

/**
 * Execute payout for a climate token
 */
export const executePayout = async (token_uid: string, data: ExecutePayoutRequest): Promise<ExecutePayoutResponse> => {
  try {
    const response = await hathorApi.post<ExecutePayoutResponse>(`/tokens/${token_uid}/payout`, data);
    return response.data;
  } catch (error) {
    console.error('Error executing payout:', error);
    throw error;
  }
};

/**
 * List all climate tokens
 */
export const listTokens = async (status?: string, index_type?: string): Promise<TokenInfo[]> => {
  try {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (index_type) params.index_type = index_type;

    const response = await hathorApi.get<TokenInfo[]>('/tokens', { params });
    return response.data;
  } catch (error) {
    console.error('Error listing tokens:', error);
    throw error;
  }
};

/**
 * Get token information by UID
 */
export const getTokenInfo = async (token_uid: string): Promise<TokenInfo> => {
  try {
    const response = await hathorApi.get<TokenInfo>(`/tokens/${token_uid}`);
    return response.data;
  } catch (error) {
    console.error('Error getting token info:', error);
    throw error;
  }
};

/**
 * Get climate index from oracle
 */
export const getClimateIndex = async (data: ClimateIndexRequest): Promise<ClimateIndexResponse> => {
  try {
    const response = await hathorApi.post<ClimateIndexResponse>('/oracle/index', data);
    return response.data;
  } catch (error) {
    console.error('Error getting climate index:', error);
    throw error;
  }
};

/**
 * Get wallet balance for a token
 */
export const getWalletBalance = async (token_uid: string): Promise<WalletBalanceResponse> => {
  try {
    const response = await hathorApi.get<WalletBalanceResponse>(`/wallet/balance/${token_uid}`);
    return response.data;
  } catch (error) {
    console.error('Error getting wallet balance:', error);
    throw error;
  }
};

/**
 * Get transaction status
 */
export const getTransactionStatus = async (tx_hash: string): Promise<any> => {
  try {
    const response = await hathorApi.get(`/transaction/${tx_hash}`);
    return response.data;
  } catch (error) {
    console.error('Error getting transaction status:', error);
    throw error;
  }
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format token UID for display
 */
export const formatTokenUid = (uid: string): string => {
  if (!uid) return '';
  if (uid.length <= 16) return uid;
  return `${uid.slice(0, 8)}...${uid.slice(-8)}`;
};

/**
 * Format explorer URL for display
 */
export const getExplorerLink = (explorer_url: string, type: 'token' | 'transaction' = 'token'): string => {
  if (!explorer_url) return '#';
  return explorer_url;
};

/**
 * Get token status badge color
 */
export const getTokenStatusColor = (status: string): string => {
  switch (status) {
    case 'active':
      return 'bg-green-500';
    case 'triggered':
      return 'bg-yellow-500';
    case 'paid_out':
      return 'bg-blue-500';
    case 'expired':
      return 'bg-gray-500';
    case 'cancelled':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

/**
 * Get index type icon
 */
export const getIndexTypeIcon = (index_type: string): string => {
  switch (index_type) {
    case 'drought':
      return '🏜️';
    case 'flood':
      return '🌊';
    case 'temperature':
    case 'heatwave':
      return '🌡️';
    case 'frost':
      return '❄️';
    case 'wind':
    case 'hurricane':
      return '💨';
    case 'precipitation':
      return '🌧️';
    default:
      return '📊';
  }
};

// Export default
export default {
  createClimateToken,
  createDroughtToken,
  createFloodToken,
  transferTokens,
  executePayout,
  listTokens,
  getTokenInfo,
  getClimateIndex,
  getWalletBalance,
  getTransactionStatus,
  formatTokenUid,
  getExplorerLink,
  getTokenStatusColor,
  getIndexTypeIcon,
};
