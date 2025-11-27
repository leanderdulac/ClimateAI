import { loadEmbrapaApi } from './loadEmbrapaApi';

// Helper function to build API URLs properly
function buildApiUrl(path: string): string {
    // Check if we're using mock data or real API
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (useMockData) {
        // Return a mock API route when using mock data
        return `/mock${path}`;
    }

    const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
    // Ensure proper path joining: if baseUrl is empty, return just the path
    // If baseUrl is provided, ensure it ends with a slash and then append the path
    if (!baseUrl) {
        return path;
    }
    // Ensure baseUrl ends with a slash and path doesn't start with a slash
    const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
    const normalizedPath = path.startsWith('/') ? path.substring(1) : path;
    return `${normalizedBaseUrl}${normalizedPath}`;
}

// Mock data generator functions
function generateMockPricingResult(request: PolicyPricingRequest): PolicyPricingResult {
    const assetValue = request.asset_value || 100000;
    const severityAmount = request.severity_amount || 10000;
    const frequencyPct = request.frequency_pct || 10;

    const purePremium = severityAmount * (frequencyPct / 100) * 1.1; // Factor in exposure
    const totalPremium = purePremium * 1.35; // Add loadings and margins

    return {
        is_approved: true,
        status: 'APPROVED_MOCK',
        rejection_reason: null,
        financials: {
            pure_premium: purePremium,
            risk_margin: assetValue * 0.05,
            loadings: totalPremium * 0.15,
            total_premium: totalPremium,
            op_claims_cost: totalPremium * 0.08,
            op_admin_cost: totalPremium * 0.12,
            op_subscription_cost: 150,
            total_operational_costs: totalPremium * 0.2 + 150,
            net_profit: totalPremium * 0.05,
            profit_margin_pct: 5,
            combined_ratio: 95
        },
        decision_flow: 'mock_calculated'
    };
}

interface ClimaData {
    data: string;
    temperatura: number;
    precipitacao: number;
    umidade: number;
    vento_velocidade?: number;
    vento_direcao?: number;
    pressao?: number;
}

export interface LocalizacaoData {
    latitude: number;
    longitude: number;
    cidade?: string;
    estado?: string;
    estado_nome?: string;
    formattedAddress?: string;
    cep?: string;
    bairro?: string;
    logradouro?: string;
    pais?: string;
    distanceKm?: number;
}

export const embrapaApi = {
    async getDadosHistoricos(
        latitude: number,
        longitude: number,
        dataInicio: string,
        dataFim: string
    ): Promise<ClimaData[]> {
        const embrapaApiService = await loadEmbrapaApi();
        const dados = await embrapaApiService.getClimateData(latitude, longitude, dataInicio, dataFim);
        return dados.map((item) => ({
            data: item.date,
            temperatura: item.temperature,
            precipitacao: item.precipitation,
            umidade: item.humidity,
            vento_velocidade: item.windSpeed,
            vento_direcao: item.windDirection,
            pressao: item.pressure,
        }));
    },

    async getLocalizacao(latitude: number, longitude: number): Promise<LocalizacaoData> {
        try {
            const embrapaApiService = await loadEmbrapaApi();
            const location = await embrapaApiService.getLocationData(latitude, longitude);
            return {
                latitude,
                longitude,
                cidade: location.city,
                estado: location.state,
                estado_nome: location.stateName,
                formattedAddress: location.formattedAddress,
                cep: location.postcode,
                bairro: location.bairro || location.neighborhood,
                logradouro: location.logradouro || location.street,
                pais: location.country,
                distanceKm: location.distanceKm
            };
        } catch (error) {
            console.error('Erro ao buscar localização:', error);
            return { latitude, longitude };
        }
    },

    async getDadosAtuais(latitude: number, longitude: number): Promise<ClimaData> {
        const embrapaApiService = await loadEmbrapaApi();
        const atual = await embrapaApiService.getCurrentClimate(latitude, longitude);
        return {
            data: atual.date,
            temperatura: atual.temperature,
            precipitacao: atual.precipitation,
            umidade: atual.humidity,
            vento_velocidade: atual.windSpeed,
            vento_direcao: atual.windDirection,
            pressao: atual.pressure,
        };
    },

    async getPrevisao(
        latitude: number,
        longitude: number,
        dias: number = 7
    ): Promise<ClimaData[]> {
        const embrapaApiService = await loadEmbrapaApi();
        const previsao = await embrapaApiService.getWeatherForecast(latitude, longitude, dias);
        return previsao.map((item) => ({
            data: item.date || '',
            temperatura: item.temperature,
            precipitacao: item.precipitation,
            umidade: item.humidity,
            vento_velocidade: item.windSpeed,
        }));
    },

    async getLocalizacaoPorCep(cep: string): Promise<LocalizacaoData> {
        const embrapaApiService = await loadEmbrapaApi();
        const location = await embrapaApiService.getLocationByCep(cep);
        return {
            latitude: location.latitude,
            longitude: location.longitude,
            cidade: location.city,
            estado: location.state,
            estado_nome: location.stateName,
            formattedAddress: location.formattedAddress,
            cep: location.cep ?? location.postcode,
            bairro: location.bairro || location.neighborhood,
            logradouro: location.logradouro || location.street,
            pais: location.country
        };
    },

    async getLocalizacaoPorCidade(cidade: string, estado: string): Promise<LocalizacaoData> {
        const embrapaApiService = await loadEmbrapaApi();
        const location = await embrapaApiService.getLocationByCity(cidade, estado);
        return {
            latitude: location.latitude,
            longitude: location.longitude,
            cidade: location.city,
            estado: location.state,
            estado_nome: location.stateName,
            formattedAddress: location.formattedAddress,
            pais: location.country
        };
    },

    async buscarCidades(termo: string, estado?: string): Promise<LocalizacaoData[]> {
        const embrapaApiService = await loadEmbrapaApi();
        const cidades = await embrapaApiService.searchCities(termo, estado);
        return cidades.map((location) => ({
            latitude: location.latitude,
            longitude: location.longitude,
            cidade: location.city,
            estado: location.state,
            estado_nome: location.stateName,
            formattedAddress: location.formattedAddress,
            pais: location.country
        }));
    }
};

// Machine Learning API
export interface MLPredictionFeatures {
    rainfall?: number;
    temperature?: number;
    humidity?: number;
    inflation_rate?: number;
    gdp_growth?: number;
    latitude?: number;
    longitude?: number;
    month?: number;
}

export interface MLPredictionResult {
    frequency: {
        prediction: number;
        confidence_lower: number;
        confidence_upper: number;
        unit: string;
    };
    severity: {
        prediction: number;
        confidence_lower: number;
        confidence_upper: number;
        unit: string;
    };
    method: string;
    confidence_level: string;
}

export const mlApi = {
    async predictSinistrality(features: MLPredictionFeatures): Promise<MLPredictionResult> {
        try {
            const url = buildApiUrl('/api/v1/modelagem/ml-sinistrality-prediction');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(features),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erro na predição ML:', error);
            throw error;
        }
    },

    async trainModels(data?: any[]): Promise<any> {
        try {
            const url = buildApiUrl('/api/v1/ml/train-models');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data || null),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro no treinamento ML:', error);
            throw error;
        }
    },

    async getModelInfo(): Promise<any> {
        try {
            const url = buildApiUrl('/api/v1/ml/model-info');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter info do modelo:', error);
            throw error;
        }
    }
};

// External API Interfaces and Functions
export interface WeatherData {
    temperature: number;
    humidity: number;
    pressure: number;
    precipitation: number;
    wind_speed: number;
    wind_direction: number;
    description: string;
    timestamp: string;
    source: string;
}

export interface EconomicData {
    inflation_rate: number;
    gdp_growth: number;
    timestamp: string;
    source: string;
}

export interface CommodityData {
    price: number;
    change: number;
    change_percent: number;
    volume: number;
    timestamp: string;
    source: string;
}

export interface RealTimeData {
    weather: WeatherData;
    economic: EconomicData;
    commodities: { [symbol: string]: CommodityData };
    timestamp: string;
    location: { latitude: number; longitude: number };
    error?: string;
}

export const externalApi = {
    async getWeatherData(latitude: number, longitude: number): Promise<WeatherData> {
        try {
            const url = buildApiUrl(`/api/v1/external/weather?latitude=${latitude}&longitude=${longitude}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter dados meteorológicos:', error);
            throw error;
        }
    },

    async getEconomicIndicators(): Promise<EconomicData> {
        try {
            const url = buildApiUrl('/api/v1/external/economic-indicators');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter indicadores econômicos:', error);
            throw error;
        }
    },

    async getCommodityPrices(symbols: string[]): Promise<{ [symbol: string]: CommodityData }> {
        try {
            const symbolsParam = symbols.join(',');
            const url = buildApiUrl(`/api/v1/external/commodity-prices?symbols=${symbolsParam}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter preços de commodities:', error);
            throw error;
        }
    },

    async getXWeatherForecast(latitude: number, longitude: number, days: number = 7): Promise<any[]> {
        try {
            const url = buildApiUrl(`/api/v1/xweather/brazil-forecast?latitude=${latitude}&longitude=${longitude}&days=${days}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result.forecast_data || [];
        } catch (error) {
            console.error('Erro ao obter previsão da API xWeather:', error);
            throw error;
        }
    },

    async getRealTimeData(latitude: number, longitude: number, commodities?: string[]): Promise<RealTimeData> {
        try {
            const params = new URLSearchParams({
                latitude: latitude.toString(),
                longitude: longitude.toString(),
            });

            if (commodities && commodities.length > 0) {
                params.append('commodities', commodities.join(','));
            }

            const url = buildApiUrl(`/api/v1/external/real-time-data?${params}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter dados em tempo real:', error);
            throw error;
        }
    }
};

// Microsegmentation Interfaces and Functions
export interface Microsegment {
    id: string;
    centroid: { latitude: number; longitude: number };
    bounds: {
        min_lat: number;
        max_lat: number;
        min_lon: number;
        max_lon: number;
    };
    point_count: number;
    risk_profile: {
        weather_risk: number;
        soil_risk: number;
        economic_risk: number;
        infrastructure_risk: number;
        overall_risk: number;
    };
    risk_category: string;
    coordinates: number[][];
}

export interface MicrosegmentationResult {
    region_bounds: any;
    total_microsegments: number;
    microsegments: Microsegment[];
    clustering_info: {
        algorithm: string;
        n_clusters: number;
        silhouette_score: number;
    };
    timestamp: string;
    error?: string;
}

export interface LocationRiskAnalysis {
    location: { latitude: number; longitude: number };
    microsegment: Microsegment;
    distance_to_centroid: number;
    is_within_bounds: boolean;
    risk_analysis: {
        overall_risk: number;
        risk_category: string;
        risk_factors: any;
        recommendations: string[];
    };
    timestamp: string;
    error?: string;
}

export interface MicrosegmentationSummary {
    region_id: string;
    total_microsegments: number;
    risk_statistics: {
        mean_risk: number;
        std_risk: number;
        min_risk: number;
        max_risk: number;
        risk_categories: { [category: string]: number };
    };
    clustering_info: any;
    timestamp: string;
    error?: string;
}

export const microsegmentationApi = {
    async createMicrosegments(regionBounds: any, nSegments: number = 20): Promise<MicrosegmentationResult> {
        try {
            const url = buildApiUrl(`/api/v1/microsegmentation/create?n_segments=${nSegments}`);
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(regionBounds),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao criar microsegmentos:', error);
            throw error;
        }
    },

    async analyzeLocationRisk(latitude: number, longitude: number, regionId: string = 'default'): Promise<LocationRiskAnalysis> {
        try {
            const url = buildApiUrl(`/api/v1/microsegmentation/analyze-location?latitude=${latitude}&longitude=${longitude}&region_id=${regionId}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao analisar risco da localização:', error);
            throw error;
        }
    },

    async getMicrosegmentationSummary(regionId: string = 'default'): Promise<MicrosegmentationSummary> {
        try {
            const url = buildApiUrl(`/api/v1/microsegmentation/summary?region_id=${regionId}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter resumo de microsegmentação:', error);
            throw error;
        }
    }
};

// Audit and Compliance Interfaces and Functions
export interface AuditLogEntry {
    id: string;
    timestamp: string;
    operation: string;
    resource_type: string;
    action: string;
    status: string;
    user_id?: string;
    session_id?: string;
    resource_id?: string;
    details?: any;
    risk_score?: number;
    compliance_flags?: string[];
}

export interface ComplianceReport {
    period: {
        start_date: string;
        end_date: string;
    };
    summary: {
        total_operations: number;
        successful_operations: number;
        failed_operations: number;
        compliance_violations: number;
    };
    violations: Array<{
        id: string;
        timestamp: string;
        operation: string;
        violation_type: string;
        severity: string;
        description: string;
        resolution_status: string;
    }>;
    risk_distribution: {
        low: number;
        medium: number;
        high: number;
        critical: number;
    };
    timestamp: string;
}

export interface AlertEntry {
    id: string;
    type: string;
    severity: string;
    message: string;
    audit_log_id?: string;
    operation?: string;
    details: {
        compliance_flags?: string[];
        additional_data?: any;
        resolution_notes?: string;
    };
    timestamp: string;
    acknowledged: boolean;
    resolved: boolean;
}

export interface AlertStats {
    total_alerts: number;
    unacknowledged: number;
    unresolved: number;
    severity_counts: Record<string, number>;
    recent_alerts: number;
}

export interface AlertSummary {
    total_alerts: number;
    unacknowledged_alerts: number;
    unresolved_alerts: number;
    by_severity: {
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
    by_type: Record<string, number>;
}

export const auditApi = {
    async getAuditLogs(params?: {
        start_date?: string;
        end_date?: string;
        operation?: string;
        user_id?: string;
        status?: string;
        limit?: number;
    }): Promise<AuditLogEntry[]> {
        try {
            const queryParams = new URLSearchParams();
            if (params) {
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        queryParams.append(key, value.toString());
                    }
                });
            }

            const url = buildApiUrl(`/api/v1/audit/logs?${queryParams}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter logs de auditoria:', error);
            throw error;
        }
    },

    async getComplianceReport(params?: {
        start_date?: string;
        end_date?: string;
    }): Promise<ComplianceReport> {
        try {
            const queryParams = new URLSearchParams();
            if (params) {
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        queryParams.append(key, value.toString());
                    }
                });
            }

            const url = buildApiUrl(`/api/v1/audit/compliance/report?${queryParams}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter relatório de compliance:', error);
            throw error;
        }
    },

    async logOperation(params: {
        operation: string;
        resource_type: string;
        action: string;
        status?: string;
        user_id?: string;
        session_id?: string;
        resource_id?: string;
        details?: any;
        risk_score?: number;
        compliance_flags?: string[];
    }): Promise<{ audit_id: string; message: string }> {
        try {
            const url = buildApiUrl('/api/v1/audit/log-operation');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao registrar operação:', error);
            throw error;
        }
    },

    // Alert management functions
    async getAlerts(params?: {
        acknowledged?: boolean;
        resolved?: boolean;
        severity?: string;
        limit?: number;
        offset?: number;
    }): Promise<{ alerts: AlertEntry[]; total_count: number; limit: number; offset: number }> {
        try {
            const queryParams = new URLSearchParams();
            if (params) {
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        queryParams.append(key, value.toString());
                    }
                });
            }

            const url = buildApiUrl(`/api/v1/audit/alerts?${queryParams}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter alertas:', error);
            throw error;
        }
    },

    async acknowledgeAlert(alertId: string): Promise<{ message: string }> {
        try {
            const url = buildApiUrl(`/api/v1/audit/alerts/${alertId}/acknowledge`);
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao reconhecer alerta:', error);
            throw error;
        }
    },

    async resolveAlert(alertId: string, resolutionNotes?: string): Promise<{ message: string }> {
        try {
            const url = buildApiUrl(`/api/v1/audit/alerts/${alertId}/resolve`);
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ resolution_notes: resolutionNotes }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao resolver alerta:', error);
            throw error;
        }
    },

    async getAlertStats(): Promise<AlertStats> {
        try {
            const url = buildApiUrl('/api/v1/audit/alerts/stats');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter estatísticas de alertas:', error);
            throw error;
        }
    },

    async getAlertSummary(): Promise<AlertSummary> {
        try {
            const url = buildApiUrl('/api/v1/audit/alerts/summary');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro ao obter resumo de alertas:', error);
            throw error;
        }
    }
};

// Pricing API
export interface PricingRequest {
    location_id: string;
    coverage_amount: number;
    coverage_period: number;
    user_id?: string;
    session_id?: string;
}

export interface PricingResult {
    final_price: number;
    risk_score: number;
    risk_factors: {
        climatic_risk: number;
        economic_risk: number;
        location_risk: number;
    };
    recommendations: string[];
    compliance_flags: string[];
    audit_id: string;
}

export const pricingApi = {
    async calculatePricing(request: PricingRequest): Promise<PricingResult> {
        try {
            const url = buildApiUrl('/api/v1/pricing/calculate');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro no cálculo de pricing:', error);
            throw error;
        }
    }
};

// Interfaces para Derivativos Climáticos
export interface ClimateDerivativePricingRequest {
    target_year: number;
    iam_adjustment?: number;
    scenario_name?: string;
    months_to_expiry?: number;
}

export interface ClimateDerivativePricingResult {
    cdd_analysis: {
        average_cdd: number;
        cdd_distribution: number[];
    };
    temperature_projection: {
        mean: number;
        std: number;
        distribution: number[];
    };
    risk_metrics: {
        expected_payout: number;
        var_95: number;
        cvar_95: number;
        var_99: number;
        cvar_99: number;
    };
    pricing: {
        bid_price: number;
        ask_price: number;
        spread: number;
    };
    sensitivity_analysis: Record<string, {
        bid_price: number;
        ask_price: number;
        var_95: number;
    }>;
    methodology: {
        gaussian_process: boolean;
        monte_carlo_simulations: number;
        risk_analysis: boolean;
        inmet_integration: boolean;
    };
    timestamp: string;
}

export interface ScenarioComparisonRequest {
    scenarios: ClimateDerivativePricingRequest[];
}

export interface ScenarioComparisonResult {
    scenario_results: ClimateDerivativePricingResult[];
    comparison_summary: {
        best_scenario: string;
        worst_scenario: string;
        average_risk: number;
        total_spread_range: number;
    };
}

export interface RiskAnalysisRequest {
    target_year: number;
    confidence_level?: number;
}

export interface RiskAnalysisResult {
    risk_metrics: {
        var_95: number;
        cvar_95: number;
        var_99: number;
        cvar_99: number;
        expected_shortfall: number;
    };
    stress_tests: {
        scenario: string;
        loss_amount: number;
        probability: number;
    }[];
    recommendations: string[];
}

export interface INMETValidationRequest {
    station_code: string;
    start_date: string;
    end_date: string;
}

export interface INMETValidationResult {
    station_data: {
        code: string;
        name: string;
        location: {
            latitude: number;
            longitude: number;
        };
    };
    temperature_data: {
        date: string;
        temperature_celsius: number;
        temperature_fahrenheit: number;
        cdd_contribution: number;
    }[];
    validation_summary: {
        total_days: number;
        average_temperature: number;
        total_cdd: number;
        data_quality_score: number;
    };
}

export interface CapitalAnalysisRequest {
    ask_price: number;
    initial_capital?: number;
    risk_tolerance?: number;
}

export interface CapitalAnalysisResult {
    capital_analysis: {
        initial_capital: number;
        ask_price_per_contract: number;
        contracts_affordable: number;
        recommended_contracts: number;
        total_investment: number;
        estimated_realized_spread: number;
        return_on_capital_percent: number;
        capital_efficiency: number;
    };
    investment_strategies: {
        conservative: { max_contracts: number; description: string };
        moderate: { max_contracts: number; description: string };
        aggressive: { max_contracts: number; description: string };
    };
    recommendation: {
        type: string;
        message: string;
        risk_assessment: string;
    };
    market_context: {
        contract_price_percentile: string;
        volatility_adjustment: number;
        liquidity_note: string;
    };
}

// New Policy Pricing API
export interface PolicyPricingRequest {
    asset_value: number;
    severity_amount: number;
    frequency_pct: number;
    coverage_period_years?: number;
    scr_score?: number;
    is_manual_underwriting?: boolean;
    location_risk_zone?: string;
}

export interface FinancialBreakdown {
    pure_premium: number;
    risk_margin: number;
    loadings: number;
    total_premium: number;
    op_claims_cost: number;
    op_admin_cost: number;
    op_subscription_cost: number;
    total_operational_costs: number;
    net_profit: number;
    profit_margin_pct: number;
    combined_ratio: number;
}

export interface PolicyPricingResult {
    is_approved: boolean;
    status: string;
    rejection_reason: string | null;
    financials: FinancialBreakdown;
    decision_flow: string;
}

export const policyPricingApi = {
    async calculate(request: PolicyPricingRequest): Promise<PolicyPricingResult> {
        const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

        if (useMockData) {
            console.warn('Using mock data for policy pricing calculation');
            return generateMockPricingResult(request);
        }

        try {
            const url = buildApiUrl('/api/v1/policy-pricing/calculate');

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                const text = await response.text();
                try {
                    const errorData = JSON.parse(text);
                    if (errorData.detail) {
                        errorMessage += ` - ${errorData.detail}`;
                    } else {
                        errorMessage += ` - ${JSON.stringify(errorData)}`;
                    }
                } catch (e) {
                    errorMessage += ` - ${text.substring(0, 200)}`;
                }
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro no cálculo de apólice:', error);
            // Check if the error is related to fetching to provide better diagnostics
            if (error instanceof TypeError && error.message.includes('fetch')) {
                console.error('Falha na requisição de cálculo avançado - verifique a configuração do backend');

                // Provide mock response for development/deployment without backend
                console.warn('Using mock data for policy pricing calculation (fallback)');
                return generateMockPricingResult(request);
            }
            throw error;
        }
    }
};

export const climateDerivativesApi = {
    async calculatePricing(request: ClimateDerivativePricingRequest): Promise<ClimateDerivativePricingResult> {
        try {
            const url = buildApiUrl('/api/v1/modelagem/derivativos-climaticos/preco');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro no cálculo de derivativos climáticos:', error);
            throw error;
        }
    },

    async compareScenarios(request: ScenarioComparisonRequest): Promise<ScenarioComparisonResult> {
        try {
            const url = buildApiUrl('/api/v1/modelagem/derivativos-climaticos/comparar-cenarios');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na comparação de cenários:', error);
            throw error;
        }
    },

    async getRiskAnalysis(request: RiskAnalysisRequest): Promise<RiskAnalysisResult> {
        try {
            const params = new URLSearchParams({
                target_year: request.target_year.toString(),
                confidence_level: (request.confidence_level || 0.95).toString(),
            });

            const url = buildApiUrl(`/api/v1/modelagem/derivativos-climaticos/analise-risco?${params}`);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na análise de risco:', error);
            throw error;
        }
    },

    async validateWithINMET(request: INMETValidationRequest): Promise<INMETValidationResult> {
        try {
            const params = new URLSearchParams({
                station_code: request.station_code,
                start_date: request.start_date,
                end_date: request.end_date,
            });

            const url = buildApiUrl(`/api/v1/modelagem/derivativos-climaticos/validacao-inmet?${params}`);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na validação INMET:', error);
            throw error;
        }
    },

    async analyzeCapitalRequirements(request: CapitalAnalysisRequest): Promise<CapitalAnalysisResult> {
        try {
            const url = buildApiUrl('/api/v1/modelagem/derivativos-climaticos/analise-capital');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na análise de capital:', error);
            throw error;
        }
    }
};
