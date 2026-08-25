import { getDefaultHeaders } from '../requestId';
import { buildApiUrl } from './client';

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

export interface PolicyPricingRequest {
    asset_value: number;
    severity_amount: number;
    frequency_pct: number;
    coverage_period_years?: number;
    scr_score?: number;
    is_manual_underwriting?: boolean;
    location_risk_zone?: string;
    latitude?: number;
    longitude?: number;
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
    is_demo?: boolean;
    is_approved: boolean;
    status: string;
    rejection_reason: string | null;
    financials: FinancialBreakdown;
    fractal_metrics?: {
        hurst_exponent: number;
        fractal_dimension: number;
        regime: string;
        complexity: number;
    };
    risk_factors?: Record<string, number>;
    decision_flow: string;
}

function generateMockPricingResult(request: PolicyPricingRequest): PolicyPricingResult {
    const assetValue = request.asset_value || 100000;
    const severityAmount = request.severity_amount || 10000;
    const frequencyPct = request.frequency_pct || 10;

    const purePremium = severityAmount * (frequencyPct / 100) * 1.1;
    const totalPremium = purePremium * 1.35;

    return {
        is_demo: true,
        is_approved: true,
        status: 'DEMO_ONLY',
        rejection_reason: 'Dados simulados. Nao usar para cotacao real.',
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

function validatePolicyPricingResult(payload: Record<string, unknown>): PolicyPricingResult {
    const fin = payload?.financials as Record<string, unknown> | undefined;
    if (
        !fin ||
        typeof fin.total_premium !== 'number' ||
        typeof fin.net_profit !== 'number' ||
        typeof fin.pure_premium !== 'number'
    ) {
        throw new Error('Resposta de pricing inválida: financials ausente ou malformado');
    }

    const fractal = payload.fractal_metrics as Record<string, unknown> | undefined;

    return {
        is_demo: Boolean(payload.is_demo) || String(payload.status ?? '').includes('DEMO'),
        is_approved: Boolean(payload.is_approved),
        status: String(payload.status ?? ''),
        rejection_reason: (payload.rejection_reason as string | null) ?? null,
        financials: {
            pure_premium: Number(fin.pure_premium),
            risk_margin: Number(fin.risk_margin ?? 0),
            loadings: Number(fin.loadings ?? 0),
            total_premium: Number(fin.total_premium),
            op_claims_cost: Number(fin.op_claims_cost ?? 0),
            op_admin_cost: Number(fin.op_admin_cost ?? 0),
            op_subscription_cost: Number(fin.op_subscription_cost ?? 0),
            total_operational_costs: Number(fin.total_operational_costs ?? 0),
            net_profit: Number(fin.net_profit),
            profit_margin_pct: Number(fin.profit_margin_pct ?? 0),
            combined_ratio: Number(fin.combined_ratio ?? 0),
        },
        fractal_metrics: fractal
            ? {
                hurst_exponent: Number(fractal.hurst_exponent ?? 0),
                fractal_dimension: Number(fractal.fractal_dimension ?? 0),
                regime: String(fractal.regime ?? ''),
                complexity: Number(fractal.complexity ?? 0),
            }
            : undefined,
        decision_flow: String(payload.decision_flow ?? ''),
    };
}

export const pricingApi = {
    async calculatePricing(request: PricingRequest): Promise<PricingResult> {
        const url = buildApiUrl('/api/v1/pricing/calculate');
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                ...getDefaultHeaders(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json() as PricingResult;
    }
};

export const policyPricingApi = {
    async calculate(request: PolicyPricingRequest): Promise<PolicyPricingResult> {
        const useMockData = !import.meta.env.PROD && import.meta.env.VITE_USE_MOCK_DATA === 'true';

        if (useMockData) {
            console.warn('Using explicit demo pricing (VITE_USE_MOCK_DATA=true)');
            return generateMockPricingResult(request);
        }

        const url = buildApiUrl('/api/v1/pricing/quote');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    ...getDefaultHeaders(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                signal: controller.signal
            });

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                const text = await response.text().catch(() => '');
                try {
                    const errorData = JSON.parse(text) as { detail?: unknown };
                    if (errorData.detail) {
                        errorMessage += ` - ${errorData.detail}`;
                    } else {
                        errorMessage += ` - ${JSON.stringify(errorData)}`;
                    }
                } catch {
                    errorMessage += ` - ${text.substring(0, 200)}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json() as Record<string, unknown>;
            return validatePolicyPricingResult(result);
        } catch (error: unknown) {
            console.error('Erro no cálculo de apólice:', error);
            if (error instanceof Error && error.name === 'AbortError') {
                throw new Error('Tempo esgotado ao calcular o premio. Tente novamente.');
            }
            throw error;
        } finally {
            clearTimeout(timeoutId);
        }
    }
};
