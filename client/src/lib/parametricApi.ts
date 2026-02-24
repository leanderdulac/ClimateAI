import { buildApiUrl } from "./api";
import { getDefaultHeaders } from "./requestId";

export interface PayoutTierReport {
    total_registros: number;
    eventos_gatilho: number;
    taxa_disparo: number;
    payout_total_estimado: number;
    payout_medio_evento: number;
    chuva_maxima: number;
    chuva_media: number;
    fontes_utilizadas: string[];
}

export interface RecentDataSample {
    data: string;
    acumulado_mm: number;
    lat: number;
    lon: number;
    fonte: string;
    payout_value: number;
    payout_pct: number;
    tier_name: string;
    triggered: boolean;
    rainfall_mm: number;
}

export interface HybridSimulationResponse {
    success: boolean;
    municipio: string;
    uf: string;
    period: string;
    report: PayoutTierReport;
    recent_data_sample: RecentDataSample[];
    error?: string;
}

export interface SIPSPerformanceSummary {
    dashboard_summary: {
        period_analyzed: {
            start_date: string;
            end_date: string;
            days_spanned: number;
        };
        current_metrics: {
            taxa_sinistralidade: number;
            sinistralidade_climatica: number;
            margem_liquida: number;
            rejeicoes: number;
            premio_medio: number;
            retencao_clientes: number;
            capital_economico: number;
        };
        improvements: {
            claim_rate_improvement: string;
            climate_loss_improvement: string;
            margin_improvement: string;
            retention_improvement: string;
            premium_growth: string;
        };
        sips_impact_score: number;
        snapshots_count: number;
    };
    statistics: Record<string, any>;
    key_findings: string[];
}

export interface RealTimeRiskAnalysis {
    timestamp: string;
    summary: {
        total_alerts: number;
        impacted_policies_count: number;
        total_exposure: number;
        potential_payout: number;
        risk_level: string;
    };
    impacted_policies: Array<{
        policy_id: string;
        policy_number: string;
        location: string;
        coverage_amount: number;
        alert_title: string;
        severity: string;
        disaster_type: string;
        potential_payout: number;
    }>;
    active_alerts: Array<{
        alert_id: string;
        title: string;
        state: string;
        severity: string;
        type: string;
    }>;
}

export const parametricApi = {
    /**
     * Simula o gatilho de Pagamento Paramétrico (Tiers 30%, 60%, 100%)
     * baseados no HybridClimateIndex (CEMADEN ArcGIS + OpenMeteo)
     */
    async simulateHybridIndex(
        municipio: string,
        uf: string,
        dataInicio: string,
        dataFim: string,
        insuredCapital: number = 100000.0
    ): Promise<HybridSimulationResponse> {
        try {
            const queryParams = new URLSearchParams({
                municipio,
                uf,
                data_inicio: dataInicio,
                data_fim: dataFim,
                insured_capital: insuredCapital.toString()
            });

            const url = buildApiUrl(`/api/v1/parametric-triggers/simulate-hybrid?${queryParams.toString()}`);
            const res = await fetch(url, { headers: getDefaultHeaders() });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `Error simulating parametric payout: ${res.status}`);
            }
            return await res.json();
        } catch (error) {
            console.error("Failed to simulate parametric payout:", error);
            throw error;
        }
    },

    /**
     * Busca o resumo de performance global (SIPS Analytics)
     */
    async getPerformanceSummary(): Promise<SIPSPerformanceSummary> {
        try {
            const url = buildApiUrl(`/api/v1/sips-analytics/dashboard-summary`);
            const res = await fetch(url, { headers: getDefaultHeaders() });
            if (!res.ok) {
                throw new Error(`Error fetching performance summary: ${res.status}`);
            }
            return await res.json();
        } catch (error) {
            console.error("Failed to fetch performance summary:", error);
            throw error;
        }
    },

    /**
     * Busca análise de risco em tempo real do portfólio
     */
    async getPortfolioRisk(): Promise<RealTimeRiskAnalysis> {
        try {
            const url = buildApiUrl(`/api/v1/risk-monitor/portfolio-risk`);
            const res = await fetch(url, { headers: getDefaultHeaders() });
            if (!res.ok) {
                throw new Error(`Error fetching portfolio risk: ${res.status}`);
            }
            return await res.json();
        } catch (error) {
            console.error("Failed to fetch portfolio risk:", error);
            throw error;
        }
    }
};
