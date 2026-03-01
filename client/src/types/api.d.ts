/**
 * Tipos TypeScript gerados a partir do OpenAPI Schema do ClimateWise
 * 
 * Para regenerar: npm run api:types
 * Ou manualmente: npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.d.ts
 */

export interface paths {
  "/health": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              status: string;
              version: string;
            };
          };
        };
      };
    };
  };
  "/api/v1/clima/historico": {
    get: {
      parameters: {
        query: {
          latitude: number;
          longitude: number;
          data_inicio: string;
          data_fim: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": {
              data: ClimaData[];
              source: string;
            };
          };
        };
      };
    };
  };
  "/api/v1/policy-pricing/calculate": {
    post: {
      requestBody: {
        content: {
          "application/json": PolicyPricingRequest;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": PolicyPricingResponse;
          };
        };
      };
    };
  };
  "/api/v1/localizacao/cidade/busca": {
    get: {
      parameters: {
        query: {
          termo: string;
          estado?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": CidadeInfo[];
          };
        };
      };
    };
  };
}

export interface ClimaData {
  data: string;
  temperatura?: number;
  temperatura_maxima?: number;
  temperatura_minima?: number;
  precipitacao?: number;
  umidade?: number;
  vento_velocidade?: number;
  vento_direcao?: number;
  pressao?: number;
  radiacao_solar?: number;
}

export interface PolicyPricingRequest {
  asset_value: number;
  severity_amount: number;
  frequency_pct: number;
  coverage_type?: string;
  location?: {
    latitude: number;
    longitude: number;
  };
}

export interface PolicyPricingResponse {
  status: "APPROVED" | "REJECTED" | "REVIEW_REQUIRED";
  financials: {
    total_premium: number;
    expected_loss: number;
    risk_premium: number;
    loading: number;
    profit_margin: number;
  };
  risk_metrics: {
    frequency: number;
    severity: number;
    loss_ratio: number;
    combined_ratio: number;
  };
  metadata: {
    calculation_date: string;
    model_version: string;
    confidence_level: number;
  };
}

export interface CidadeInfo {
  cidade: string;
  estado: string;
  latitude: number;
  longitude: number;
  ibge_codigo?: string;
}

export interface HealthCheckResponse {
  status: "healthy" | "unhealthy";
  version: string;
  timestamp?: string;
  services?: {
    database?: ServiceHealth;
    redis?: ServiceHealth;
    external_apis?: ServiceHealth;
  };
}

export interface ServiceHealth {
  status: "healthy" | "degraded" | "unhealthy";
  response_time_ms?: number;
  message?: string;
}

export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: {
    id: string;
    email: string;
    role: string;
  };
}

export interface ParametricInsuranceRequest {
  location: {
    latitude: number;
    longitude: number;
  };
  trigger: {
    type: "precipitation" | "temperature" | "wind" | "drought";
    threshold: number;
    period_days: number;
  };
  coverage: {
    sum_insured: number;
    premium_rate?: number;
  };
}

export interface ParametricInsuranceResponse {
  trigger_verified: boolean;
  payout_amount: number;
  payout_percentage: number;
  data_source: string;
  verification_date: string;
  historical_data: Array<{
    date: string;
    value: number;
  }>;
}

export interface Components {
  schemas: {
    ClimaData: ClimaData;
    PolicyPricingRequest: PolicyPricingRequest;
    PolicyPricingResponse: PolicyPricingResponse;
    CidadeInfo: CidadeInfo;
    HealthCheckResponse: HealthCheckResponse;
    AuthRequest: AuthRequest;
    AuthResponse: AuthResponse;
    ParametricInsuranceRequest: ParametricInsuranceRequest;
    ParametricInsuranceResponse: ParametricInsuranceResponse;
  };
}

// Tipo utilitário para respostas da API
export type ApiResponse<T> = {
  data: T;
  success: boolean;
  message?: string;
  request_id?: string;
};

// Tipo para paginação
export type PaginatedResponse<T> = {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

// Tipos para erros
export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
  status_code?: number;
  request_id?: string;
}
