import { buildApiUrl } from './client';
import { fetchWithTracking } from '@/lib/requestId';

export interface EnsembleFanPoint {
  time_utc: string;
  time_local: string;
  temperature_p10_c: number | null;
  temperature_p50_c: number | null;
  temperature_p90_c: number | null;
  precip_p10_mm: number | null;
  precip_p50_mm: number | null;
  precip_p90_mm: number | null;
}

export interface EnsembleDaily {
  date: string;
  member_count: number;
  temperature_mean_c: number;
  temperature_min_c: number;
  temperature_max_c: number;
  precip_mean_mm: number;
  temperature_p10_c: number;
  temperature_p50_c: number;
  temperature_p90_c: number;
  precip_p10_mm: number;
  precip_p50_mm: number;
  precip_p90_mm: number;
  precip_exceedance: Record<string, number>;
  heat_exceedance: Record<string, number>;
  p_heavy_rain: number;
}

export interface EnsembleForecast {
  latitude: number;
  longitude: number;
  model: string;
  hourly_fan: EnsembleFanPoint[];
  daily: EnsembleDaily[];
  pricing_exceedance: {
    precip_exceedance: Record<string, number>;
    heat_exceedance: Record<string, number>;
    p_heavy_rain: number;
    horizon_days: number;
  };
  timezone_daily: string;
  license?: { provider: string; terms?: string; url?: string };
  municipality?: { ibge_code: string; name: string; uf: string };
}

export interface BrazilGridCell {
  lat: number;
  lon: number;
  p_heavy_rain: number;
}

export interface BrazilGridSummary {
  resolution_deg: number;
  cell_count: number;
  p_heavy_rain_mean: number;
  p_heavy_rain_max: number;
  cells: BrazilGridCell[];
  heavy_rain_threshold_mm: number;
}

export const weathernextApi = {
  async getPoint(lat: number, lon: number): Promise<EnsembleForecast> {
    const url = buildApiUrl(
      `/api/v1/forecast/ensemble?lat=${encodeURIComponent(String(lat))}&lon=${encodeURIComponent(String(lon))}`
    );
    const response = await fetchWithTracking(url);
    if (!response.ok) {
      throw new Error(`WeatherNext ensemble failed (${response.status})`);
    }
    return response.json();
  },

  async getMunicipality(ibgeCode: string): Promise<EnsembleForecast> {
    const url = buildApiUrl(`/api/v1/forecast/ensemble/municipality/${encodeURIComponent(ibgeCode)}`);
    const response = await fetchWithTracking(url);
    if (!response.ok) {
      throw new Error(`WeatherNext municipality failed (${response.status})`);
    }
    return response.json();
  },

  async getBrazilGrid(resolution = 1): Promise<BrazilGridSummary> {
    const url = buildApiUrl(`/api/v1/forecast/ensemble/brazil?resolution=${encodeURIComponent(String(resolution))}`);
    const response = await fetchWithTracking(url);
    if (!response.ok) {
      throw new Error(`WeatherNext Brazil grid failed (${response.status})`);
    }
    return response.json();
  },
};
