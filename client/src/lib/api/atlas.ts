import { buildApiUrl } from './client';
import {
  classifyProbeStatus,
  fetchWithAuthRetry,
  type ProbeStatus,
} from './authenticatedFetch';

export interface OracleStatus {
  total_events_processed?: number;
  total_payouts_triggered?: number;
  total_blockchain_transactions?: number;
}

export interface PortfolioRiskSummary {
  total_exposure?: number;
  potential_payout?: number;
  total_alerts?: number;
  high_severity_count?: number;
  impacted_policies_count?: number;
}

export interface BlockchainTransaction {
  tx_id?: string;
  confirmations?: number;
  amount?: number;
}

export interface PortfolioRisk {
  summary?: PortfolioRiskSummary;
  blockchain_transactions?: BlockchainTransaction[];
}

export interface LiveEvent {
  event_id?: string;
  disaster_type: string;
  severity_score: number;
  payout_triggered?: boolean;
  payout_amount?: number;
  description?: string;
  timestamp?: string;
  municipio?: string;
  uf?: string;
  latitude?: number;
  longitude?: number;
  source?: string;
}

export interface WeatherCurrent {
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  precipitation?: number;
  weather_description?: string;
}

export interface WeatherRiskIndicators {
  risk_level?: string;
}

export interface WeatherCityData {
  city: string;
  source?: string;
  current?: WeatherCurrent;
  risk_indicators?: WeatherRiskIndicators;
}

export interface SpaceWeather {
  geomagnetic_storm_active?: boolean;
  kp_index?: number;
  solar_flux?: number;
  status?: string;
  timestamp?: string;
}

export interface ConjunctionAlert {
  satellite_1: string;
  satellite_2: string;
  miss_distance_km: number;
  probability: string;
  tca_time: string;
}

export interface ConjunctionsData {
  alerts?: ConjunctionAlert[];
}

export interface NewsAlert {
  alert_id: string;
  title: string;
  summary: string;
  source: string;
  source_url: string;
  published: string;
  disaster_type: string;
  severity: string;
  severity_score: number;
  locations: string[];
  uf: string | null;
  confidence: number;
}

export interface AtlasConnectionStatus {
  backend: ProbeStatus;
  oracle: ProbeStatus;
  blockchain: ProbeStatus;
  weather: ProbeStatus;
  celestrak: ProbeStatus;
}

export interface AtlasDashboardPayload {
  oracleStatus: OracleStatus;
  portfolioRisk: PortfolioRisk;
  liveEvents: LiveEvent[];
  realtimeWeather: WeatherCityData[];
  riskSummary: Record<string, unknown> | null;
  spaceWeather: SpaceWeather | null;
  conjunctions: ConjunctionsData | null;
  connections: AtlasConnectionStatus;
}

export const ATLAS_STATUS_ENDPOINTS = {
  backend: '/api/v1/health',
  oracle: '/api/v1/atlas-simulation/oracle-status',
  blockchain: '/api/v1/blockchain/base/status',
  weather: '/api/v1/atlas-realtime/health',
  celestrak: '/api/v1/celestrak/space-weather',
} as const;

async function readJson<T>(response: Response | undefined, fallback: T): Promise<T> {
  if (!response?.ok) {
    return fallback;
  }
  try {
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function fetchAtlasDashboard(): Promise<AtlasDashboardPayload> {
  const [
    backendRes,
    oracleRes,
    blockchainRes,
    weatherHealthRes,
    celestrakRes,
    portfolioRes,
    eventsRes,
    weatherSummaryRes,
    allCitiesRes,
    conjunctionsRes,
    integrationHealthRes,
  ] = await Promise.allSettled([
    fetchWithAuthRetry(buildApiUrl(ATLAS_STATUS_ENDPOINTS.backend)),
    fetchWithAuthRetry(buildApiUrl(ATLAS_STATUS_ENDPOINTS.oracle)),
    fetchWithAuthRetry(buildApiUrl(ATLAS_STATUS_ENDPOINTS.blockchain)),
    fetchWithAuthRetry(buildApiUrl(ATLAS_STATUS_ENDPOINTS.weather)),
    fetchWithAuthRetry(buildApiUrl(ATLAS_STATUS_ENDPOINTS.celestrak)),
    fetchWithAuthRetry(buildApiUrl('/api/v1/atlas-simulation/portfolio-risk')),
    fetchWithAuthRetry(buildApiUrl('/api/v1/atlas-simulation/live-events?limit=10')),
    fetchWithAuthRetry(buildApiUrl('/api/v1/atlas-realtime/risk-summary')),
    fetchWithAuthRetry(buildApiUrl('/api/v1/atlas-realtime/all-cities')),
    fetchWithAuthRetry(buildApiUrl('/api/v1/celestrak/conjunctions')),
    fetchWithAuthRetry(buildApiUrl('/api/v1/atlas-integration/health')),
  ]);

  const fulfilled = (result: PromiseSettledResult<Response>) =>
    result.status === 'fulfilled' ? result.value : undefined;

  const backend = fulfilled(backendRes);
  const oracle = fulfilled(oracleRes);
  const blockchain = fulfilled(blockchainRes);
  const weatherHealth = fulfilled(weatherHealthRes);
  const celestrak = fulfilled(celestrakRes);
  const portfolio = fulfilled(portfolioRes);
  const events = fulfilled(eventsRes);
  const weatherSummary = fulfilled(weatherSummaryRes);
  const allCities = fulfilled(allCitiesRes);
  const conjunctions = fulfilled(conjunctionsRes);
  void fulfilled(integrationHealthRes);

  const citiesJson = await readJson<{ data?: WeatherCityData[] }>(allCities, { data: [] });

  return {
    oracleStatus: await readJson<OracleStatus>(oracle, {
      total_events_processed: 0,
      total_payouts_triggered: 0,
    }),
    portfolioRisk: await readJson<PortfolioRisk>(portfolio, {
      summary: {
        total_exposure: 0,
        potential_payout: 0,
        total_alerts: 0,
        high_severity_count: 0,
        impacted_policies_count: 0,
      },
    }),
    liveEvents: await readJson<LiveEvent[]>(events, []),
    realtimeWeather: citiesJson.data || [],
    riskSummary: await readJson<Record<string, unknown> | null>(weatherSummary, null),
    spaceWeather: await readJson<SpaceWeather | null>(celestrak, null),
    conjunctions: await readJson<ConjunctionsData | null>(conjunctions, null),
    connections: {
      backend: await classifyProbeStatus(backend, { requireStatusField: true }),
      oracle: await classifyProbeStatus(oracle),
      blockchain: await classifyProbeStatus(blockchain),
      weather: await classifyProbeStatus(weatherHealth),
      celestrak: await classifyProbeStatus(celestrak),
    },
  };
}

export async function refreshNewsAlerts(limit = 20): Promise<NewsAlert[]> {
  const refreshRes = await fetchWithAuthRetry(buildApiUrl('/api/v1/news-crawler/refresh'), {
    method: 'POST',
  });
  if (!refreshRes.ok) {
    throw new Error(`news-crawler refresh ${refreshRes.status}`);
  }
  const alertsRes = await fetchWithAuthRetry(
    buildApiUrl(`/api/v1/news-crawler/alerts?limit=${limit}`)
  );
  if (!alertsRes.ok) {
    throw new Error(`news-crawler alerts ${alertsRes.status}`);
  }
  const json = (await alertsRes.json()) as { alerts?: NewsAlert[] };
  return json.alerts || [];
}

export const emptyAtlasDashboard = (): AtlasDashboardPayload => ({
  oracleStatus: { total_events_processed: 0, total_payouts_triggered: 0 },
  portfolioRisk: {
    summary: {
      total_exposure: 0,
      potential_payout: 0,
      total_alerts: 0,
      high_severity_count: 0,
      impacted_policies_count: 0,
    },
  },
  liveEvents: [],
  realtimeWeather: [],
  riskSummary: null,
  spaceWeather: null,
  conjunctions: null,
  connections: {
    backend: 'offline',
    oracle: 'offline',
    blockchain: 'offline',
    weather: 'offline',
    celestrak: 'offline',
  },
});
