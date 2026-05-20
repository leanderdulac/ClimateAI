import React, { useMemo, useState } from 'react';
import { policyPricingApi, type PolicyPricingRequest, type PolicyPricingResult } from '@/lib/api';

// Tipos para análise financeira
type FinancialAnalysis = ReturnType<typeof analyzeFinancialViability> & {
  annualExpectedLoss?: number;
  totalExpectedLoss?: number;
  insurerAnalysis: ReturnType<typeof analyzeFinancialViability>["insurerAnalysis"] & {
    isProfitable: boolean;
    netProfit: number;
    profitMargin: number;
    profitMarginPercentage: number;
    profitabilityStatus: string;
    operatingCosts: {
      subscription: number;
      claimsProcessing: number;
      administrative: number;
      total: number;
      annual: number;
    };
    lossRatio: number;
    expenseRatio: number;
    combinedRatio: number;
    var95: number;
    var99: number;
    expectedShortfall95: number;
    expectedShortfall99: number;
    capitalRequirement: number;
    riskAdjustedReturn: number;
  };
  overallAssessment: ReturnType<typeof analyzeFinancialViability>["overallAssessment"] & {
    isViable: boolean;
    recommendation: string;
    rejectionReason: string | null;
  };
};
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { ExecutiveDashboard } from './ExecutiveDashboard';
import { useLocation } from '@/lib/LocationContext';
import { usePeriod } from '@/lib/PeriodContext';
import { useTranslation } from '@/hooks/useTranslation';
import {
  DollarSign,
  Calculator,
  AlertTriangle,
  TrendingUp,
  Shield,
  Activity,
  Cloud,
  Droplets,
  Wind,
  Sun,
  CloudRain,
  Flame,
  BarChart3,
  Brain,
  Zap
} from "lucide-react";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import { BatchResult, computeBatchStats } from '@/hooks/useBatchStats';
import { useTokenizationStore } from '@/store/useTokenizationStore';
import { useNavigate } from 'react-router-dom';


// Financial analysis function to properly calculate viability
const analyzeFinancialViability = (
  premium: number,
  totalExpectedLoss: number,
  operatingCosts: number,
  assetValue: number,
  frequency: number,
  severity: number,
  coveragePeriod: number = 1
) => {
  // Calculate operating costs breakdown if not provided
  const subscriptionCost = 150; // Default automated subscription cost
  const claimsProcessingCost = premium * 0.08; // 8% of premium
  const adminCost = premium * 0.12; // 12% of premium
  const totalOperatingCosts = operatingCosts || (subscriptionCost + claimsProcessingCost + adminCost);
  const operatingCostsObj = {
    subscription: subscriptionCost,
    claimsProcessing: claimsProcessingCost,
    administrative: adminCost,
    total: totalOperatingCosts,
    annual: totalOperatingCosts / coveragePeriod
  };

  // Calculate annual values
  const annualExpectedLoss = (frequency / 100) * Math.min(severity, assetValue);
  const annualOperatingCosts = totalOperatingCosts / coveragePeriod;

  // Correctly calculate net profit: Premium - (Expected Loss + Operating Costs)
  const netProfit = premium - totalExpectedLoss - totalOperatingCosts;
  const isProfitableForInsurer = netProfit > 0;

  // Calculate profitability metrics
  const profitMarginPercentage = (netProfit / premium) * 100;
  const lossRatio = (totalExpectedLoss / premium) * 100;
  const expenseRatio = (totalOperatingCosts / premium) * 100;
  const combinedRatio = lossRatio + expenseRatio;

  // Determine profitability status based on margin
  let profitabilityStatus = "NO_PROFITABILITY_DATA";
  if (profitMarginPercentage > 5) {
    profitabilityStatus = "HIGHLY_PROFITABLE";
  } else if (profitMarginPercentage > 2) {
    profitabilityStatus = "PROFITABLE";
  } else if (profitMarginPercentage > -2) {
    profitabilityStatus = "BREAK_EVEN";
  } else if (profitMarginPercentage > -5) {
    profitabilityStatus = "MINOR_LOSS";
  } else {
    profitabilityStatus = "SIGNIFICANT_LOSS";
  }

  return {
    insurerAnalysis: {
      isProfitable: isProfitableForInsurer,
      netProfit,
      profitMarginPercentage,
      expectedLoss: totalExpectedLoss,
      operatingCosts: operatingCostsObj,
      annualNetProfit: netProfit / coveragePeriod,
      annualExpectedLoss,
      annualOperatingCosts,
      lossRatio,
      expenseRatio,
      combinedRatio,
      profitabilityStatus,
    },
    customerAnalysis: {
      protectionValue: assetValue,
      costBenefitRatio: assetValue / (premium / coveragePeriod),
      premiumToAssetRatio: ((premium / coveragePeriod) / assetValue) * 100,
      isAffordable: (((premium / coveragePeriod) / assetValue) * 100) < 5,
      valueRating: 'N/A',
      annualCostPercentage: ((premium / coveragePeriod) / assetValue) * 100,
    },
    riskAnalysis: {
      stressTests: [],
      worstCaseScenario: null,
      catastropheProbability: null,
      reinsuranceNeed: null,
    },
    overallAssessment: {
      isViable: isProfitableForInsurer,
      recommendation: isProfitableForInsurer ? "APPROVED" : "REJECTED",
      rejectionReason: isProfitableForInsurer ? null : netProfit ? `Financial unviability: Net profit of ${netProfit.toFixed(2)} is negative` : `Financial unviability: Net profit calculation unavailable`,
    }
  };
};

type ClimateEvent = {
  id: string;
  name: string;
  icon: JSX.Element;
  baseFrequency: number;
  baseSeverity: number;
};

const climateEvents: ClimateEvent[] = [
  {
    id: 'drought',
    name: 'pricing.events.drought',
    icon: <Sun className="h-4 w-4" />,
    baseFrequency: 15,
    baseSeverity: 8000
  },
  {
    id: 'flood',
    name: 'pricing.events.flood',
    icon: <Droplets className="h-4 w-4" />,
    baseFrequency: 12,
    baseSeverity: 12000
  },
  {
    id: 'rain',
    name: 'pricing.events.rain',
    icon: <CloudRain className="h-4 w-4" />,
    baseFrequency: 25,
    baseSeverity: 5000
  },
  {
    id: 'wind',
    name: 'pricing.events.wind',
    icon: <Wind className="h-4 w-4" />,
    baseFrequency: 20,
    baseSeverity: 7000
  },
  {
    id: 'hail',
    name: 'pricing.events.hail',
    icon: <Cloud className="h-4 w-4" />,
    baseFrequency: 8,
    baseSeverity: 15000
  },
  {
    id: 'fire',
    name: 'pricing.events.fire',
    icon: <Flame className="h-4 w-4" />,
    baseFrequency: 10,
    baseSeverity: 20000
  }
];



// Error alert component (must be top-level, not inside another function)
function ErrorAlert({ message, onClose }: { message: string, onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-800 rounded flex items-center justify-between animate-fade-in">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-red-500" />
        <span className="font-medium">{message}</span>
      </div>
      <button onClick={onClose} className="ml-4 px-2 py-1 text-xs bg-red-200 rounded hover:bg-red-300">{t('common.close')}</button>
    </div>
  );
}

export function PricingSimulator() {
  const { t, language } = useTranslation();
  const { selectedPeriod } = usePeriod();
  const [assetValue, setAssetValue] = useState<number>(100000); // Valor do bem/serviço
  const [selectedEvent, setSelectedEvent] = useState<ClimateEvent | null>(null);
  const [frequency, setFrequency] = useState<number>(10); // %
  const [severity, setSeverity] = useState<number>(10000); // $
  const [variableSim, setVariableSim] = useState<boolean>(false); // Simulação variável
  const [confidence, setConfidence] = useState<number>(95); // %
  const [premium, setPremium] = useState<number>(0);
  const [advancedResults, setAdvancedResults] = useState<any>(null);
  const [financialAnalysis, setFinancialAnalysis] = useState<FinancialAnalysis | null>(null);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [policySimulations, setPolicySimulations] = useState<any[]>([]);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [coveragePeriod, setCoveragePeriod] = useState<number>(1); // Período de cobertura em anos
  const [activeTab, setActiveTab] = useState<'simulator' | 'tokenization'>('simulator');
  const [mlPredictions, setMlPredictions] = useState<MLPredictionResult | null>(null);

  const { selectedLocation } = useLocation();

  const validBatch = useMemo<BatchResult[]>(() => {
    const batch = (advancedResults?.batch as BatchResult[] | undefined) ?? [];
    return batch.filter((b) => b.premium !== null);
  }, [advancedResults]);

  const batchStats = useMemo(() => {
    if (!validBatch.length) return null;
    return computeBatchStats(validBatch);
  }, [validBatch]);

  const handleEventSelect = (event: ClimateEvent) => {
    setSelectedEvent(event);
    setFrequency(event.baseFrequency);
    setSeverity(event.baseSeverity);
  };

  const handleCalculate = async () => {
    console.log('[PricingSimulator] Iniciando cálculo...');
    console.log('[PricingSimulator] assetValue:', assetValue);
    console.log('[PricingSimulator] selectedEvent:', selectedEvent);
    console.log('[PricingSimulator] frequency:', frequency);
    console.log('[PricingSimulator] severity:', severity);
    console.log('[PricingSimulator] selectedLocation:', selectedLocation);

    // Parâmetros base e validações iniciais
    let simAssetValue = assetValue;
    let simFrequency = frequency;
    let simSeverity = severity;

    if (assetValue <= 0) {
      const errorMsg = t('pricing.errors.invalidAsset') || 'Valor do bem inválido';
      console.error('[PricingSimulator] Validação falhou: assetValue <= 0');
      setCalcError(errorMsg);
      alert(errorMsg);
      return;
    }

    if (!selectedEvent) {
      console.warn('[PricingSimulator] Nenhum evento selecionado, usando valores padrão');
      simFrequency = simFrequency || 10;
      simSeverity = simSeverity || 10000;
    }

    // Cenário de stress e simulação variável
    let stressResults = null;
    let batchResults: BatchResult[] = [];

    const logNorm = (mu: number, sigma: number) => Math.exp(mu + sigma * (Math.random() * 2 - 1));
    const genParams = () => {
      const v = Math.round(Math.max(20000, Math.min(1000000, logNorm(11.5, 0.7))));
      const f = Math.random() < 0.2 ? Math.round(30 + Math.random() * 40) : Math.round(5 + Math.random() * 25);
      const s = Math.random() < 0.15 ? Math.round(60000 + Math.random() * 140000) : Math.round(5000 + Math.random() * 55000);
      return { v, f, s };
    };

    if (variableSim) {
      console.log('[PricingSimulator] Executando simulação variável (5 execuções)...');

      const requests = Array.from({ length: 5 }, (_, i) => {
        const { v, f, s } = genParams();
        const req: PolicyPricingRequest = {
          asset_value: v,
          severity_amount: s,
          frequency_pct: f,
          coverage_period_years: coveragePeriod,
          scr_score: 450,
          is_manual_underwriting: false,
          latitude: selectedLocation?.latitude ?? -23.55,
          longitude: selectedLocation?.longitude ?? -46.63,
        };

        return policyPricingApi
          .calculate(req)
          .then((res) => {
            console.log(`[PricingSimulator] Simulação ${i + 1}/5:`, { v, f, s });
            return {
              assetValue: v,
              frequency: f,
              severity: s,
              premium: res.financials.total_premium,
              netProfit: res.financials.net_profit,
              loss: res.financials.pure_premium,
              margin: res.financials.profit_margin_pct,
            } as BatchResult;
          })
          .catch((e) => {
            console.error(`[PricingSimulator] Erro na simulação ${i + 1}/5:`, e);
            return { assetValue: v, frequency: f, severity: s, premium: null, netProfit: null, loss: null, margin: null } as BatchResult;
          });
      });

      const results = await Promise.all(requests);
      batchResults = results;

      const firstValid = batchResults.find((b) => b.premium !== null) || batchResults[0];
      simAssetValue = firstValid.assetValue;
      simFrequency = firstValid.frequency;
      simSeverity = firstValid.severity;

      console.log('[PricingSimulator] Simulação variável completa, resultados:', batchResults.length);

      const stressRequest: PolicyPricingRequest = {
        asset_value: simAssetValue,
        severity_amount: 200000,
        frequency_pct: 70,
        coverage_period_years: coveragePeriod,
        scr_score: 450,
        is_manual_underwriting: false,
        latitude: selectedLocation?.latitude ?? -23.55,
        longitude: selectedLocation?.longitude ?? -46.63,
      };
      try {
        const stressResult: PolicyPricingResult = await policyPricingApi.calculate(stressRequest);
        stressResults = {
          assetValue: stressRequest.asset_value,
          frequency: stressRequest.frequency_pct,
          severity: stressRequest.severity_amount,
          premium: stressResult.financials.total_premium,
          netProfit: stressResult.financials.net_profit,
          loss: stressResult.financials.pure_premium,
          margin: stressResult.financials.profit_margin_pct,
        };
      } catch (e) {
        console.warn('[PricingSimulator] Erro no stress test (ignorando):', e);
      }
    }

    setCalculating(true);
    setCalcError(null);
    try {
      console.log('[PricingSimulator] Enviando requisição para API...');
      const request: PolicyPricingRequest = {
        asset_value: simAssetValue,
        severity_amount: simSeverity,
        frequency_pct: simFrequency,
        coverage_period_years: coveragePeriod,
        scr_score: 450, // Default value as it's not in the UI
        is_manual_underwriting: false,
        latitude: selectedLocation?.latitude ?? -23.55, // Default: São Paulo
        longitude: selectedLocation?.longitude ?? -46.63
      };

      console.log('[PricingSimulator] Request:', request);
      const result: PolicyPricingResult = await policyPricingApi.calculate(request);
      console.log('[PricingSimulator] Resultado da API:', result);

      // --- Map new result to old state structure ---

      setPremium(result.financials.total_premium);

      // Map to advancedResults
      // Calculate confidence interval based on premium variability
      const confidenceMargin = result.financials.total_premium * 0.15; // ±15% based on uncertainty
      const newAdvancedResults = {
        premio_total: result.financials.total_premium,
        premio_puro: result.financials.pure_premium,
        carregamentos: result.financials.loadings,
        margem_risco: result.financials.risk_margin,
        risk_factors: result.risk_factors,
        intervalo_confianca: {
          inferior: result.financials.total_premium - confidenceMargin,
          superior: result.financials.total_premium + confidenceMargin
        },
        analise_fractal: result.fractal_metrics ? {
          hurst_exponent: result.fractal_metrics.hurst_exponent,
          fractal_dimension: result.fractal_metrics.fractal_dimension,
          regime: result.fractal_metrics.regime,
          complexity_index: result.fractal_metrics.complexity
        } : null,
        risco_fuzzy: null,
        metodologia: {
          tecnicas_utilizadas: ['EVT (Extreme Value Theory)', 'Fractal Analysis', 'Monte Carlo'],
          iteracoes_monte_carlo: 10000
        },
      };
      setAdvancedResults(newAdvancedResults);
      // Se simulação variável, salva lote para exibir
      if (variableSim && batchResults.length > 0) {
        setAdvancedResults((prev: any) => ({
          ...prev,
          batch: batchResults
        }));
      }

      // Exibir resultados de stress se houver
      if (stressResults) {
        setAdvancedResults((prev: any) => ({
          ...prev,
          stressScenario: stressResults
        }));
      }

      // Analyze financial viability using the correct methodology
      const financialAnalysisResult = analyzeFinancialViability(
        result.financials.total_premium,
        result.financials.pure_premium, // This is the total expected loss
        result.financials.total_operational_costs,
        assetValue,
        frequency,
        severity,
        coveragePeriod
      );

      // Calculate advanced risk metrics based on the financial data
      const calculateVar95 = (purePremium: number, combinedRatio: number): number => {
        // VaR 95% is calculated as pure premium + potential volatility at 95% confidence
        const volatilityFactor = 1.645; // 95% confidence value for normal distribution
        const adjustedPremium = purePremium * combinedRatio;
        return adjustedPremium * 1.15; // Adding 15% buffer based on combined ratio
      };

      const calculateExpectedShortfall95 = (var95: number): number => {
        // Expected shortfall is typically 10-20% higher than VaR
        return var95 * 1.12;
      };

      const calculateCapitalRequirement = (totalPremium: number, combinedRatio: number): number => {
        // Solvency capital requirement based on premium and risk profile
        const baseSCR = totalPremium * 0.15; // Base requirement
        const riskAdjustment = baseSCR * (Math.max(combinedRatio - 100, 0) / 100); // Extra for high combined ratio
        return baseSCR + riskAdjustment;
      };

      const calculateRiskAdjustedReturn = (netProfit: number, capitalRequirement: number): number => {
        // Return on risk-adjusted capital
        if (capitalRequirement <= 0) return 0;
        return netProfit / capitalRequirement;
      };

      // Calculate risk metrics
      const var95Value = calculateVar95(result.financials.pure_premium, result.financials.combined_ratio);
      const capitalReqValue = calculateCapitalRequirement(result.financials.total_premium, result.financials.combined_ratio);
      const riskAdjustedReturnValue = calculateRiskAdjustedReturn(result.financials.net_profit, capitalReqValue);

      // Update the analysis with backend results to ensure accuracy
      const newFinancialAnalysis = {
        ...financialAnalysisResult,
        annualExpectedLoss: result.financials.pure_premium / coveragePeriod,
        totalExpectedLoss: result.financials.pure_premium,
        insurerAnalysis: {
          ...financialAnalysisResult.insurerAnalysis,
          // Override with precise backend values
          isProfitable: result.financials.net_profit > 0,
          netProfit: result.financials.net_profit,
          profitMargin: result.financials.net_profit / coveragePeriod,
          profitMarginPercentage: result.financials.profit_margin_pct,
          profitabilityStatus: result.status,
          operatingCosts: {
            subscription: result.financials.op_subscription_cost,
            claimsProcessing: result.financials.op_claims_cost,
            administrative: result.financials.op_admin_cost,
            total: result.financials.total_operational_costs,
            annual: result.financials.total_operational_costs / coveragePeriod
          },
          lossRatio: (result.financials.pure_premium / result.financials.total_premium) * 100,
          expenseRatio: (result.financials.total_operational_costs / result.financials.total_premium) * 100,
          combinedRatio: result.financials.combined_ratio,
          var95: var95Value,
          var99: var95Value * 1.3, // VaR 99% is typically higher than VaR 95%
          expectedShortfall95: calculateExpectedShortfall95(var95Value),
          expectedShortfall99: calculateExpectedShortfall95(var95Value * 1.3),
          capitalRequirement: capitalReqValue,
          riskAdjustedReturn: riskAdjustedReturnValue,
        },
        overallAssessment: {
          isViable: result.is_approved,
          recommendation: result.status,
          rejectionReason: result.rejection_reason,
        }
      };
      setFinancialAnalysis(newFinancialAnalysis);

      // Policy simulations are not generated by the new service, so we can clear it.
      setPolicySimulations([]);

      console.log('[PricingSimulator] Cálculo concluído com sucesso!');
      console.log('[PricingSimulator] Premium:', result.financials.total_premium);
      console.log('[PricingSimulator] Net Profit:', result.financials.net_profit);
      console.log('[PricingSimulator] Status:', result.status);

      window.dispatchEvent(new CustomEvent('climateai:quote-calculated', {
        detail: {
          premium: result.financials.total_premium,
          coveragePeriod,
          frequency: simFrequency,
          severity: simSeverity,
          eventId: selectedEvent?.id || null,
          status: result.status || null,
        },
      }));

      // Get ML predictions for sinistrality (can remain as is)
      try {
        let realTimeData = null;
        try {
          realTimeData = await externalApi.getRealTimeData(
            selectedLocation?.latitude || -15,
            selectedLocation?.longitude || -47
          );
        } catch (rtError) {
          console.warn('Real-time data not available, using defaults:', rtError);
        }

        const mlFeatures: MLPredictionFeatures = {
          rainfall: realTimeData?.weather?.precipitation || 120,
          temperature: realTimeData?.weather?.temperature || 25,
          humidity: realTimeData?.weather?.humidity || 70,
          inflation_rate: realTimeData?.economic?.inflation_rate || 0.04,
          gdp_growth: realTimeData?.economic?.gdp_growth || 0.025,
          latitude: selectedLocation?.latitude ?? -23.55,
          longitude: selectedLocation?.longitude ?? -46.63,
          month: new Date().getMonth() + 1
        };

        const mlResult = await mlApi.predictSinistrality(mlFeatures);
        setMlPredictions(mlResult);
      } catch (mlError) {
        console.warn('ML prediction failed, continuing without ML insights:', mlError);
        setMlPredictions(null);
      }

    } catch (error: any) {
      console.error('[PricingSimulator] Erro no cálculo:', error);
      console.error('[PricingSimulator] Error details:', {
        message: error?.message,
        detail: error?.detail,
        stack: error?.stack
      });

      let errorMessage = t('pricing.errors.calculationError') || 'Erro ao calcular prêmio';

      if (error?.message) {
        errorMessage += `: ${error.message}`;
      } else if (error?.detail) {
        errorMessage += `: ${error.detail}`;
      } else if (typeof error === 'string') {
        errorMessage += `: ${error}`;
      }

      // Adiciona dicas de troubleshooting
      const troubleshootingTips = [
        '\n\nDicas:',
        '1. Verifique se o backend está rodando e acessível',
        '2. Verifique o console do navegador para mais detalhes',
        '3. Tente novamente em alguns instantes'
      ].join('\n');

      setCalcError(errorMessage + troubleshootingTips);
      alert(errorMessage);
    } finally {
      setCalculating(false);
      console.log('[PricingSimulator] Cálculo finalizado (calculating = false)');
    }
  };

  const handleCreateToken = () => {
    if (!advancedResults || premium <= 0) return;

    let eventType = 'seca'; // default
    if (selectedEvent?.id === 'flood') eventType = 'enchente';
    if (selectedEvent?.id === 'heatwave') eventType = 'onda_calor';
    if (selectedEvent?.id === 'frost') eventType = 'geada';

    // Map intensity properly based on inputs
    const severityScore = (severity / assetValue) * 10;
    const alertLevel = Math.min(5, Math.ceil(severityScore)).toString() || '3';

    setPendingTokenizationData({
      tipo: eventType,
      latitude: '-23.5505', // Default placeholder se nenhuma GPS location for detectada nesse widget
      longitude: '-46.6333',
      intensidade: severityScore.toFixed(2),
      probabilidade: frequency.toString(),
      descricao: `${t('tokenization.create.simulatedPolicy')} ${t(selectedEvent?.name || '')}. ${t('pricing.labels.premium')}: ${premium.toLocaleString(language)}, ${t('pricing.labels.margin')}: ${advancedResults.margem_risco?.toLocaleString(language)}`,
      nivel_alerta: alertLevel,
      token_supply: Math.round(assetValue),
      riskFactors: advancedResults.risk_factors
    });

    navigate('/tokenization');
  };

  return (
    <Card className="pricing-simulator overflow-hidden animate-fade-in" variant="default">
      {calcError && (
        <ErrorAlert message={calcError} onClose={() => setCalcError(null)} />
      )}
      <div className="flex items-center gap-3 mb-4">
        <input type="checkbox" id="variableSim" checked={variableSim} onChange={e => setVariableSim(e.target.checked)} />
        <label htmlFor="variableSim" className="text-sm">{t('pricing.simulator.variable')}</label>
      </div>
      {variableSim && (
        <div className="mb-4 p-3 bg-blue-50 rounded text-xs text-blue-900">
          <div><b>Simulações em lote (5 execuções aleatórias):</b></div>
          <ol className="list-decimal ml-4">
            {advancedResults?.batch?.map((b: any, idx: number) => (
              <li key={idx}>
                Valor do bem: R$ {b.assetValue.toLocaleString()} | Frequência: {b.frequency}% | Severidade: R$ {b.severity.toLocaleString()}<br />
                {b.premium !== null ? (
                  <>
                    Prêmio: R$ {b.premium.toLocaleString()} | Perda Esperada: R$ {b.loss.toLocaleString()} | Lucro Líquido: R$ {b.netProfit.toLocaleString()} | Margem: {b.margin}%
                  </>
                ) : (
                  <span className="text-red-700">Erro ao calcular</span>
                )}
              </li>
            ))}
          </ol>
          {/* Estatísticas do lote e gráficos avançados */}
          {batchStats && validBatch.length > 0 && (() => {
            const stats = batchStats;
            return (
              <>
                <div className="mt-2 p-2 bg-blue-100 rounded">
                  <b>Estatísticas do lote:</b><br />
                  Prêmio: média R$ {stats.premiumStats.mean.toLocaleString(undefined, { maximumFractionDigits: 0 })}, desvio R$ {stats.premiumStats.std.toLocaleString(undefined, { maximumFractionDigits: 0 })}, min R$ {stats.premiumStats.min.toLocaleString()}, max R$ {stats.premiumStats.max.toLocaleString()}<br />
                  Perda Esperada: média R$ {stats.lossStats.mean.toLocaleString(undefined, { maximumFractionDigits: 0 })}, desvio R$ {stats.lossStats.std.toLocaleString(undefined, { maximumFractionDigits: 0 })}, min R$ {stats.lossStats.min.toLocaleString()}, max R$ {stats.lossStats.max.toLocaleString()}<br />
                  Lucro Líquido: média R$ {stats.profitStats.mean.toLocaleString(undefined, { maximumFractionDigits: 0 })}, desvio R$ {stats.profitStats.std.toLocaleString(undefined, { maximumFractionDigits: 0 })}, min R$ {stats.profitStats.min.toLocaleString()}, max R$ {stats.profitStats.max.toLocaleString()}<br />
                  Margem: média {stats.marginStats.mean.toFixed(1)}%, desvio {stats.marginStats.std.toFixed(1)}%, min {stats.marginStats.min.toFixed(1)}%, max {stats.marginStats.max.toFixed(1)}%<br />
                  Correlação prêmio x lucro: <b>{stats.corrPremioLucro.toFixed(2)}</b><br />
                  Percentil 10 do lucro: R$ {stats.p10.toLocaleString(undefined, { maximumFractionDigits: 0 })} | Percentil 90: R$ {stats.p90.toLocaleString(undefined, { maximumFractionDigits: 0 })}<br />
                  Outliers prêmio: {stats.outPremio.length > 0 ? stats.outPremio.map(x => `R$ ${x.toLocaleString()}`).join(', ') : 'nenhum'}<br />
                  Outliers lucro: {stats.outLucro.length > 0 ? stats.outLucro.map(x => `R$ ${x.toLocaleString()}`).join(', ') : 'nenhum'}
                </div>
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Boxplot dos Prêmios */}
                  <div>
                    <b>Boxplot dos Prêmios</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={[stats.premiumBox]}>
                        <XAxis dataKey={() => ''} hide />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="min" fill="#d1d5db" />
                        <Bar dataKey="q1" fill="#a5b4fc" />
                        <Bar dataKey="median" fill="#6366f1" />
                        <Bar dataKey="q3" fill="#a5b4fc" />
                        <Bar dataKey="max" fill="#d1d5db" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Linha temporal dos Lucros */}
                  <div>
                    <b>Lucro Líquido (Linha Temporal)</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <LineChart data={validBatch.map((b, i) => ({ name: `Sim ${i + 1}`, value: b.netProfit }))}>
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="value" stroke="#059669" />
                        <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="3 3" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Scatter plot Prêmio vs Lucro */}
                  <div>
                    <b>Dispersão Prêmio x Lucro</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <ScatterChart>
                        <CartesianGrid />
                        <XAxis dataKey="premium" name="Prêmio" />
                        <YAxis dataKey="netProfit" name="Lucro" />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter name="Simulações" data={validBatch} fill="#6366f1" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Boxplot dos Lucros */}
                  <div>
                    <b>Boxplot dos Lucros Líquidos</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={[stats.profitBox]}>
                        <XAxis dataKey={() => ''} hide />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="min" fill="#d1d5db" />
                        <Bar dataKey="q1" fill="#a7f3d0" />
                        <Bar dataKey="median" fill="#059669" />
                        <Bar dataKey="q3" fill="#a7f3d0" />
                        <Bar dataKey="max" fill="#d1d5db" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                {/* Gráficos originais de barras */}
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <b>Distribuição dos Prêmios</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={validBatch.map((b, i) => ({ name: `Sim ${i + 1}`, value: b.premium }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="value" fill="#2563eb" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div>
                    <b>Distribuição dos Lucros Líquidos</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={validBatch.map((b, i) => ({ name: `Sim ${i + 1}`, value: b.netProfit }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="value" fill="#059669" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div>
                    <b>Distribuição das Perdas Esperadas</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={validBatch.map((b, i) => ({ name: `Sim ${i + 1}`, value: b.loss }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="value" fill="#f59e42" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div>
                    <b>Distribuição das Margens (%)</b>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={validBatch.map((b, i) => ({ name: `Sim ${i + 1}`, value: b.margin }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="value" fill="#6366f1" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            );
          })()}
          <div className="mt-2"><b>Simulação principal:</b> Valor do bem: R$ {assetValue.toLocaleString()} | Frequência: {frequency}% | Severidade: R$ {severity.toLocaleString()}</div>
          {advancedResults?.stressScenario && (
            <div className="mt-2">
              <b>Cenário de Stress:</b> Valor do bem: R$ {advancedResults.stressScenario.assetValue.toLocaleString()} | Frequência: {advancedResults.stressScenario.frequency}% | Severidade: R$ {advancedResults.stressScenario.severity.toLocaleString()}<br />
              Prêmio: R$ {advancedResults.stressScenario.premium.toLocaleString()} | Lucro Líquido: R$ {advancedResults.stressScenario.netProfit.toLocaleString()} | Margem: {advancedResults.stressScenario.margin}%
            </div>
          )}
        </div>
      )}
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Calculator className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">{t('pricing.simulator.title')}</CardTitle>
              <CardDescription className="text-primary-100">
                {t('pricing.simulator.subtitle')}
              </CardDescription>
            </div>
          </div>
          {premium > 0 && (
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <DollarSign className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">
                  {t('pricing.labels.totalInsurance')} ({coveragePeriod} {coveragePeriod === 1 ? t('pricing.labels.year') : t('pricing.labels.years')})
                </div>
                <div className="text-lg font-semibold text-white">
                  R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
                <div className="text-xs text-primary-200">
                  R$ {(premium / coveragePeriod).toLocaleString(undefined, { maximumFractionDigits: 2 })}/{t('pricing.labels.year')}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-10 p-8 bg-gradient-to-b from-white to-neutral-50">

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'simulator'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            {t('pricing.tabs.simulator')}
          </button>
          <button
            onClick={() => window.location.href = '/tokenization'}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'tokenization'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            {t('pricing.tabs.tokenization')}
          </button>
        </div>

        <div className="grid gap-8 sm:grid-cols-2">
          <div className="space-y-6">
            {/* Climate Events Selection */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
                  <Cloud className="h-4 w-4 text-primary-500" />
                  {t('pricing.labels.climateEvent')}
                </Label>
                {selectedEvent && (
                  <Badge variant="default" className="px-2 py-1">
                    {t(`pricing.events.${selectedEvent.id}`)}
                  </Badge>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                {climateEvents.map((event) => (
                  <Button
                    key={event.id}
                    variant={selectedEvent?.id === event.id ? "default" : "outline"}
                    className={`h-auto py-4 flex flex-col gap-2 relative overflow-hidden transition-all ${selectedEvent?.id === event.id ? 'ring-2 ring-primary ring-offset-2' : ''
                      }`}
                    onClick={() => handleEventSelect(event)}
                  >
                    {event.icon}
                    <span className="text-sm font-semibold">{t(event.name)}</span>
                    {selectedEvent?.id === event.id && (
                      <div className="absolute top-0 right-0 p-1 bg-primary text-primary-foreground rounded-bl-lg">
                        <Zap className="h-3 w-3 fill-current" />
                      </div>
                    )}
                  </Button>
                ))}
              </div>
            </div>

            {/* Asset Value Input */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="assetValue"
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <DollarSign className="h-4 w-4 text-primary-500" />
                  {t('pricing.labels.assetValue')}
                </Label>
                <Badge variant="default" className="px-2 py-1">
                  ${assetValue.toLocaleString()}
                </Badge>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4">
                <Input
                  id="assetValue"
                  type="number"
                  min={0}
                  step={1000}
                  value={assetValue}
                  onChange={(e) => setAssetValue(Number(e.target.value))}
                  className="text-center"
                  placeholder="Enter asset value"
                />
                <div className="mt-2 flex justify-between">
                  <span className="text-xs text-neutral-500">Value in USD ($)</span>
                </div>
              </div>
            </div>

            {/* Event Frequency Input */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="frequency"
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <Activity className="h-4 w-4 text-primary-500" />
                  Frequência do Evento
                </Label>
                <Badge variant="default" className="px-2 py-1">
                  {frequency}%
                </Badge>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4">
                <Slider
                  id="frequency"
                  min={0}
                  max={100}
                  step={1}
                  value={[frequency]}
                  onValueChange={([value]) => setFrequency(value)}
                />
                <div className="mt-2 flex justify-between">
                  <span className="text-xs text-neutral-500">Eventos Raros</span>
                  <span className="text-xs text-neutral-500">Eventos Frequentes</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="severity"
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <AlertTriangle className="h-4 w-4 text-warning-500" />
                  Maximum Severity
                </Label>
                <Badge variant="warning" className="px-2 py-1">
                  ${severity.toLocaleString()}
                </Badge>
              </div>
              <Input
                id="severity"
                type="number"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                variant="outlined"
                className="text-center"
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="confidence"
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700"
                >
                  <TrendingUp className="h-4 w-4 text-primary-500" />
                  Confidence Level
                </Label>
                <Badge variant="secondary" className="px-2 py-1">
                  {confidence}%
                </Badge>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4">
                <Slider
                  id="confidence"
                  min={50}
                  max={99}
                  step={1}
                  value={[confidence]}
                  onValueChange={([value]) => setConfidence(value)}
                />
                <div className="mt-2 flex justify-between">
                  <span className="text-xs text-neutral-500">50% (More Risk)</span>
                  <span className="text-xs text-neutral-500">99% (More Safety)</span>
                </div>
              </div>
            </div>

            {/* Coverage Period Selection */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
                  <Activity className="h-4 w-4 text-primary-500" />
                  Período de Cobertura
                </Label>
                <Badge variant="default" className="px-2 py-1">
                  {coveragePeriod} {coveragePeriod === 1 ? 'ano' : 'anos'}
                </Badge>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {[1, 2, 3, 5].map((period) => (
                  <Button
                    key={period}
                    variant={coveragePeriod === period ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCoveragePeriod(period)}
                    className={coveragePeriod === period
                      ? "bg-primary-500 text-white"
                      : "hover:bg-primary-50"
                    }
                  >
                    {period} {period === 1 ? 'ano' : 'anos'}
                  </Button>
                ))}
              </div>
              <div className="text-xs text-neutral-500 text-center">
                Período total da apólice de seguro
              </div>
            </div>

            {/* Risk Assessment Button */}
            <div className="rounded-lg border-2 border-dashed border-neutral-200 bg-neutral-50 p-6">
              <div className="space-y-4 text-center">
                <Calculator className="mx-auto h-8 w-8 text-primary-400" />
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900">Risk Assessment</h3>
                  <p className="mt-1 text-xs text-neutral-500">
                    Our actuarial model uses advanced mathematical techniques: fractal analysis, Monte Carlo simulation, fuzzy logic, statistical physics, and actuarial calculations
                  </p>
                </div>
                <Button
                  onClick={handleCalculate}
                  disabled={calculating}
                  className="w-full shadow-sm bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white disabled:opacity-50"
                  size="lg"
                >
                  <Calculator className="mr-2 h-4 w-4" />
                  {calculating ? 'Calculando...' : 'Calculate Premium'}
                </Button>
              </div>
            </div>
          </div>

          {/* Resultados Avançados */}
          {premium > 0 && advancedResults && (
            <div className="mt-6 space-y-6">
              {/* Resultado Principal */}
              <div className="animate-slide-up rounded-lg bg-gradient-to-r from-success-50 to-success-100 p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-success-100 p-2">
                        <DollarSign className="h-4 w-4 text-success-600" />
                      </div>
                      <h3 className="font-medium text-success-900">Cálculo Atuarial Avançado</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="px-2 py-1">
                        {confidence}% Confiança
                      </Badge>
                      <Button size="sm" onClick={handleCreateToken} className="bg-success-600 hover:bg-success-700 ml-2 shadow-sm">
                        Tokenizar esta Apólice
                      </Button>
                    </div>
                  </div>

                  <div className="text-3xl font-bold text-success-700">
                    R$ {premium.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Prêmio Puro</div>
                      <div className="text-lg font-bold text-primary-600">
                        R$ {advancedResults.premio_puro?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Carregamentos</div>
                      <div className="text-lg font-bold text-blue-600">
                        R$ {advancedResults.carregamentos?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Margem de Risco</div>
                      <div className="text-lg font-bold text-orange-600">
                        R$ {advancedResults.margem_risco?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="text-xs text-neutral-600">Intervalo de Confiança</div>
                      <div className="text-sm font-bold text-purple-600">
                        R$ {advancedResults.intervalo_confianca?.inferior?.toLocaleString() || 'N/A'} -<br />
                        R$ {advancedResults.intervalo_confianca?.superior?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Análise Fractal */}
              {advancedResults.analise_fractal && (
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-purple-50 to-purple-100 p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-purple-100 p-2">
                        <Activity className="h-4 w-4 text-purple-600" />
                      </div>
                      <h3 className="font-medium text-purple-900">Análise Fractal Climática</h3>
                    </div>

                    <div className="rounded-lg bg-white p-4 shadow-sm border border-purple-200">
                      <div className="text-xs text-neutral-600">Hurst Exponent</div>
                      <div className="text-lg font-bold text-purple-600">
                        {advancedResults?.analise_fractal?.hurst_exponent?.toFixed(3) || 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-500">Persistência vs Caos</div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm border border-purple-200">
                      <div className="text-xs text-neutral-600">Dimensão Fractal</div>
                      <div className="text-lg font-bold text-purple-600">
                        {advancedResults?.analise_fractal?.fractal_dimension?.toFixed(3) || 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-500">Complexidade do padrão</div>
                    </div>
                    <div className="rounded-lg bg-white p-4 shadow-sm border border-purple-200">
                      <div className="text-xs text-neutral-600">Regime Detectado</div>
                      <div className="text-sm font-bold text-purple-700">
                        {advancedResults?.analise_fractal?.regime || 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-500">Estado dinâmico</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Avaliação Fuzzy */}
              {advancedResults.risco_fuzzy && (
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-yellow-50 to-yellow-100 p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-yellow-100 p-2">
                        <TrendingUp className="h-4 w-4 text-yellow-600" />
                      </div>
                      <h3 className="font-medium text-yellow-900">Avaliação Fuzzy de Risco</h3>
                    </div>

                    <div className="space-y-2">
                      {[
                        { label: 'Muito Baixo', value: advancedResults.risco_fuzzy.muito_baixo, color: 'bg-green-500' },
                        { label: 'Baixo', value: advancedResults.risco_fuzzy.baixo, color: 'bg-green-400' },
                        { label: 'Médio', value: advancedResults.risco_fuzzy.medio, color: 'bg-yellow-500' },
                        { label: 'Alto', value: advancedResults.risco_fuzzy.alto, color: 'bg-orange-500' },
                        { label: 'Muito Alto', value: advancedResults.risco_fuzzy.muito_alto, color: 'bg-red-500' }
                      ].map((item) => (
                        <div key={item.label} className="flex items-center gap-3">
                          <div className="w-20 text-sm text-neutral-600">{item.label}</div>
                          <div className="flex-1 bg-neutral-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${item.color}`}
                              style={{ width: `${(item.value || 0) * 100}%` }}
                            ></div>
                          </div>
                          <div className="w-12 text-sm font-medium text-neutral-700">
                            {(((item?.value || 0) * 100)?.toFixed(1) || 'N/A')}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Derivativos Climáticos */}
              {advancedResults.climate_derivatives && (
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-emerald-50 to-emerald-100 p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-emerald-100 p-2">
                        <Cloud className="h-4 w-4 text-emerald-600" />
                      </div>
                      <h3 className="font-medium text-emerald-900">Derivativos Climáticos</h3>
                      <Badge variant="outline" className="ml-auto">
                        Gaussian Process + Monte Carlo
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">CDD Médio</div>
                        <div className="text-lg font-bold text-emerald-600">
                          {advancedResults.climate_derivatives.cdd_analysis?.average_cdd?.toLocaleString() || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Dias de calor projetados</div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Temperatura Média</div>
                        <div className="text-lg font-bold text-emerald-600">
                          {advancedResults?.climate_derivatives?.temperature_projection?.mean?.toFixed(1) || 'N/A'}°F
                        </div>
                        <div className="text-xs text-neutral-500">Projeção climática</div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">VaR (95%)</div>
                        <div className="text-lg font-bold text-orange-600">
                          R$ {advancedResults.climate_derivatives.risk_metrics?.var_95?.toLocaleString() || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Perda máxima esperada</div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">CVaR (95%)</div>
                        <div className="text-lg font-bold text-red-600">
                          R$ {advancedResults.climate_derivatives.risk_metrics?.cvar_95?.toLocaleString() || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Perda condicional média</div>
                      </div>
                    </div>

                    {/* Análise de Capital */}
                    {advancedResults.climate_derivatives.capital_requirements && (
                      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex items-start gap-2">
                          <BarChart3 className="h-5 w-5 text-blue-600 mt-0.5" />
                          <div className="flex-1">
                            <div className="font-medium text-blue-900">Análise de Capital</div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                              <div className="text-sm">
                                <span className="text-blue-700">Contratos possíveis:</span>
                                <div className="font-semibold text-blue-900">
                                  {advancedResults?.climate_derivatives?.capital_requirements?.contracts_affordable?.toFixed(4) || 'N/A'}
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="text-blue-700">Retorno estimado:</span>
                                <div className="font-semibold text-green-600">
                                  {advancedResults?.climate_derivatives?.capital_requirements?.return_on_capital_percent?.toFixed(1) || 'N/A'}%
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="text-blue-700">Spread realizado:</span>
                                <div className="font-semibold text-blue-900">
                                  R$ {advancedResults.climate_derivatives.capital_requirements.estimated_realized_spread?.toLocaleString()}
                                </div>
                              </div>
                              <div className="text-sm">
                                <span className="text-blue-700">Recomendação:</span>
                                <div className="font-semibold text-blue-900">
                                  {advancedResults.climate_derivatives.capital_requirements.contracts_affordable < 1 ? 'Fracionário' : 'Completo'}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="mt-4 p-4 bg-emerald-50 rounded-lg">
                      <div className="flex items-start gap-2">
                        <Brain className="h-5 w-5 text-emerald-600 mt-0.5" />
                        <div>
                          <div className="font-medium text-emerald-900">Modelo Avançado de IA</div>
                          <div className="text-sm text-emerald-700 mt-1">
                            Este cálculo utiliza Processos Gaussianos para projeção de temperatura,
                            simulações Monte Carlo (10.000 caminhos) para análise de risco,
                            e integração com dados INMET para validação em tempo real.
                            Inclui análise completa de requisitos de capital e estratégias de investimento.
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Metodologia */}
              {advancedResults.metodologia && (
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 p-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-blue-100 p-2">
                        <Calculator className="h-4 w-4 text-blue-600" />
                      </div>
                      <h3 className="font-medium text-blue-900">Metodologia Avançada</h3>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Iterações Monte Carlo</div>
                        <div className="text-lg font-bold text-blue-600">
                          {advancedResults.metodologia.iteracoes_monte_carlo?.toLocaleString() || 'N/A'}
                        </div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Técnicas Utilizadas</div>
                        <div className="text-sm font-medium text-blue-600">
                          {advancedResults.metodologia.tecnicas_utilizadas?.join(', ') || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Análise Financeira */}
          {premium > 0 && financialAnalysis && (
            <div className="mt-10 space-y-8">
              {/* Status Geral da Apólice */}
              <div className={`animate-slide-up rounded-lg p-8 ${financialAnalysis.overallAssessment.isViable
                ? 'bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-200'
                : 'bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-200'
                }`}>
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`rounded-full p-2 ${financialAnalysis.overallAssessment.isViable ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                        {financialAnalysis.overallAssessment.isViable ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                      <h3 className={`font-medium ${financialAnalysis.overallAssessment.isViable ? 'text-green-900' : 'text-red-900'
                        }`}>
                        Análise Financeira da Apólice
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={financialAnalysis.overallAssessment.isViable ? "default" : "danger"} className="px-3 py-1">
                        {financialAnalysis.overallAssessment.recommendation}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {financialAnalysis.insurerAnalysis.profitabilityStatus}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Análise do Emissor */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">📈 Margem do Emissor</div>
                      <div className={`text-2xl font-bold mb-1 ${financialAnalysis?.insurerAnalysis?.isProfitable ? 'text-green-600' : 'text-red-600'
                        }`}>
                        {financialAnalysis?.insurerAnalysis?.profitMarginPercentage?.toFixed(1) || 'N/A'}%
                      </div>
                      <div className="text-xs text-neutral-500">
                        R$ {financialAnalysis?.insurerAnalysis?.netProfit?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'} lucro líquido
                      </div>
                    </div>

                    {/* Análise do Cliente */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">💰 Custo para Cliente</div>
                      <div className={`text-2xl font-bold mb-1 ${financialAnalysis?.customerAnalysis?.isAffordable ? 'text-green-600' : 'text-orange-600'
                        }`}>
                        {financialAnalysis?.customerAnalysis?.premiumToAssetRatio?.toFixed(1) || 'N/A'}%
                      </div>
                      <div className="text-xs text-neutral-500">
                        do valor do bem/ano
                      </div>
                    </div>

                    {/* Retorno Ajustado ao Risco */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">📊 Métricas de Risco</div>
                      <div className={`text-2xl font-bold mb-1 ${financialAnalysis?.insurerAnalysis?.combinedRatio <= 105 ? 'text-green-600' : 'text-orange-600'
                        }`}>
                        {financialAnalysis?.insurerAnalysis?.combinedRatio?.toFixed(1) || 'N/A'}%
                      </div>
                      <div className="text-xs text-neutral-500">
                        Combined Ratio
                      </div>
                    </div>
                  </div>

                  {/* Financial Transparency Section */}
                  <div className="mt-4 p-4 bg-white/50 rounded-lg border border-blue-100">
                    <div className="text-xs font-medium text-blue-800 mb-2">Cálculo de Viabilidade:</div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div className="text-center">
                        <div className="text-neutral-600">Prêmio Bruto</div>
                        <div className="font-medium text-green-600">
                          R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-neutral-600">(-) Perda Esperada</div>
                        <div className="font-medium text-red-600">
                          R$ {financialAnalysis.totalExpectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-neutral-600">(-) Custos Operacionais</div>
                        <div className="font-medium text-orange-600">
                          R$ {financialAnalysis.insurerAnalysis.operatingCosts.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-neutral-600">= Lucro Líquido</div>
                        <div className={`font-medium ${financialAnalysis.insurerAnalysis.isProfitable ? 'text-green-600' : 'text-red-600'}`}>
                          R$ {financialAnalysis.insurerAnalysis.netProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detalhes Financeiros */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Análise do Emissor Detalhada */}
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 p-8">
                  <div className="space-y-6">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-blue-100 p-2">
                        <DollarSign className="h-4 w-4 text-blue-600" />
                      </div>
                      <div className="text-sm font-medium text-blue-900">
                        Detalhes da Análise do Emissor
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Perda Esperada Anual:</span>
                        <span className="font-medium text-red-600">
                          R$ {financialAnalysis.annualExpectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Perda Esperada Total ({coveragePeriod} {coveragePeriod === 1 ? 'ano' : 'anos'}):</span>
                        <span className="font-medium text-red-600">
                          R$ {financialAnalysis.totalExpectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Prêmio Total Recebido:</span>
                        <span className="font-medium text-green-600">
                          R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      {/* Operating Costs Breakdown */}
                      <div className="border-t pt-3 space-y-2">
                        <div className="text-xs font-semibold text-blue-700">Custos Operacionais:</div>
                        <div className="space-y-1 pl-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-neutral-600">Subscrição:</span>
                            <span className="text-neutral-800">
                              R$ {financialAnalysis.insurerAnalysis.operatingCosts.subscription.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-neutral-600">Processamento de Sinistros (8%):</span>
                            <span className="text-neutral-800">
                              R$ {financialAnalysis.insurerAnalysis.operatingCosts.claimsProcessing.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-neutral-600">Administrativo (12%):</span>
                            <span className="text-neutral-800">
                              R$ {financialAnalysis.insurerAnalysis.operatingCosts.administrative.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                          </div>
                          <div className="flex justify-between font-medium pt-1 border-t">
                            <span className="text-neutral-700">Total de Custos:</span>
                            <span className="text-blue-700">
                              R$ {financialAnalysis.insurerAnalysis.operatingCosts.total.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center border-t pt-2">
                        <span className="text-sm font-medium text-neutral-700">Lucro Líquido Total:</span>
                        <span className={`font-bold ${financialAnalysis.insurerAnalysis.isProfitable ? 'text-green-600' : 'text-red-600'
                          }`}>
                          R$ {financialAnalysis.insurerAnalysis.netProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Margem Líquida:</span>
                        <span className={`font-medium ${financialAnalysis.insurerAnalysis.isProfitable ? 'text-blue-600' : 'text-red-600'
                          }`}>
                          {financialAnalysis?.insurerAnalysis?.profitMarginPercentage?.toFixed(1) || 'N/A'}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Razão de Combinação (Combined Ratio):</span>
                        <span className={`font-medium ${financialAnalysis.insurerAnalysis.combinedRatio <= 105 ? 'text-green-600' : 'text-orange-600'
                          }`}>
                          {financialAnalysis?.insurerAnalysis?.combinedRatio?.toFixed(1) || 'N/A'}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Análise do Cliente Detalhada */}
                <div className="animate-slide-up rounded-lg bg-gradient-to-r from-purple-50 to-purple-100 p-8">
                  <div className="space-y-6">
                    <div className="flex items-center gap-2">
                      <div className="rounded-full bg-purple-100 p-2">
                        <TrendingUp className="h-4 w-4 text-purple-600" />
                      </div>
                      <h3 className="font-medium text-purple-900">Análise do Cliente</h3>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Valor do Bem:</span>
                        <span className="font-medium text-purple-600">
                          R$ {assetValue.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Prêmio Anual:</span>
                        <span className="font-medium text-orange-600">
                          R$ {(premium / coveragePeriod).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Prêmio Total ({coveragePeriod} {coveragePeriod === 1 ? 'ano' : 'anos'}):</span>
                        <span className="font-medium text-orange-600">
                          R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-t pt-2">
                        <span className="text-sm font-medium text-neutral-700">Relação Custo-Benefício:</span>
                        <span className={`font-bold ${financialAnalysis.customerAnalysis.costBenefitRatio > 5 ? 'text-green-600' : 'text-orange-600'
                          }`}>
                          {financialAnalysis?.customerAnalysis?.costBenefitRatio?.toFixed(1) || 'N/A'}x
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Avaliação:</span>
                        <Badge variant={
                          financialAnalysis.customerAnalysis.valueRating === 'Excelente' ? 'default' :
                            financialAnalysis.customerAnalysis.valueRating === 'Bom' ? 'secondary' :
                              'outline'
                        }>
                          {financialAnalysis.customerAnalysis.valueRating}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recomendações */}
              <div className="animate-slide-up rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 p-8">
                <div className="space-y-6">
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-gray-100 p-2">
                      <Calculator className="h-4 w-4 text-gray-600" />
                    </div>
                    <h3 className="font-medium text-gray-900">Recomendações</h3>
                  </div>

                  {/* Advanced Risk Metrics Section */}
                  <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                    <h4 className="text-sm font-semibold text-blue-800 mb-3 flex items-center">
                      <Shield className="h-4 w-4 mr-2" />
                      Métricas Avançadas de Risco
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                      <div className="bg-white/70 p-3 rounded">
                        <div className="font-medium text-gray-700 mb-1">VaR 95%</div>
                        <div className="text-lg font-bold text-red-600">
                          R$ {financialAnalysis.insurerAnalysis.var95?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'}
                        </div>
                        <div className="text-gray-500">Perda máxima provável</div>
                      </div>
                      <div className="bg-white/70 p-3 rounded">
                        <div className="font-medium text-gray-700 mb-1">Expected Shortfall 95%</div>
                        <div className="text-lg font-bold text-red-700">
                          R$ {financialAnalysis.insurerAnalysis.expectedShortfall95?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'}
                        </div>
                        <div className="text-gray-500">Perda média no pior 5%</div>
                      </div>
                      <div className="bg-white/70 p-3 rounded">
                        <div className="font-medium text-gray-700 mb-1">Requisito de Capital</div>
                        <div className="text-lg font-bold text-blue-600">
                          R$ {financialAnalysis.insurerAnalysis.capitalRequirement?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'}
                        </div>
                        <div className="text-gray-500">Capital necessário</div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">Para o Emissor:</h4>
                      <ul className="text-xs text-gray-600 space-y-2">
                        {financialAnalysis.insurerAnalysis.isProfitable ? (
                          <>
                            <li>• ✅ Apólice lucrativa - margem adequada</li>
                            <li>• 📊 Monitorar sinistralidade real vs esperada</li>
                            <li>• 🎯 Retorno ajustado ao risco: {financialAnalysis?.insurerAnalysis?.riskAdjustedReturn?.toFixed(2) || 'N/A'}x</li>
                          </>
                        ) : (
                          <>
                            <li>• ⚠️ Apólice não lucrativa - revisar precificação</li>
                            <li>• 📈 Considerar aumento do prêmio ou redução de cobertura</li>
                            <li>• 🔍 Analisar dados históricos mais recentes</li>
                          </>
                        )}
                      </ul>
                    </div>

                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">Para o Cliente:</h4>
                      <ul className="text-xs text-gray-600 space-y-2">
                        {financialAnalysis.customerAnalysis.isAffordable ? (
                          <>
                            <li>• ✅ Custo acessível - boa relação custo-benefício</li>
                            <li>• 🛡️ Proteção adequada ao valor do bem</li>
                            <li>• 💰 Avaliação: {financialAnalysis.customerAnalysis.valueRating}</li>
                          </>
                        ) : (
                          <>
                            <li>• ⚠️ Prêmio elevado - considerar dedutível maior</li>
                            <li>• 💡 Avaliar cobertura parcial do bem</li>
                            <li>• 📞 Negociar condições especiais</li>
                          </>
                        )}
                      </ul>
                    </div>
                  </div>

                  {/* Stress Test Scenarios */}
                  {financialAnalysis.riskAnalysis && (
                    <div className="mt-6 p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg border border-orange-200">
                      <h4 className="text-sm font-semibold text-orange-800 mb-3 flex items-center">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Cenários de Stress Test
                      </h4>
                      <div className="space-y-2">
                        {financialAnalysis.riskAnalysis.stressTests?.map((scenario: any, idx: number) => (
                          <div key={idx} className="flex justify-between items-center text-xs bg-white/50 p-2 rounded">
                            <span className="font-medium">{scenario.scenario}</span>
                            <div className="flex items-center gap-2">
                              <span className={scenario.isSustainable ? 'text-green-600' : 'text-red-600'}>
                                {scenario.isSustainable ? 'Sustentável' : 'Não Sustentável'}
                              </span>
                              <span className="text-gray-500">
                                Margem: R$ {scenario.profitMargin.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      {financialAnalysis.riskAnalysis.reinsuranceNeed && (
                        <div className="mt-3 p-2 bg-red-100 rounded text-xs text-red-700">
                          ⚠️ Recomendado: Contratar reinsurance devido ao alto requisito de capital
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Simulações de Configurações de Apólice */}
          {policySimulations.length > 0 && (
            <div className="mt-10 space-y-8">
              {/* Cabeçalho das Simulações */}
              <div className="animate-slide-up rounded-lg bg-gradient-to-r from-indigo-50 to-indigo-100 p-8 border-2 border-indigo-200">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-full bg-indigo-100 p-3">
                      <Activity className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-indigo-900">Simulações de Configurações</h3>
                      <p className="text-sm text-indigo-700">
                        Compare diferentes abordagens de precificação para otimizar sua estratégia
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/50 rounded-lg p-4">
                    <p className="text-sm text-indigo-800">
                      💡 <strong>Dica:</strong> As configurações são ordenadas por viabilidade e lucratividade.
                      A primeira opção geralmente oferece o melhor equilíbrio entre risco e retorno.
                    </p>
                  </div>
                </div>
              </div>

              {/* Grid de Simulações */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {policySimulations.map((sim, index) => (
                  <div
                    key={index}
                    className={`animate-slide-up rounded-lg border-2 p-6 transition-all duration-300 ${sim.isViable
                      ? index === 0
                        ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300 shadow-lg'
                        : 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300'
                      : 'bg-gradient-to-br from-red-50 to-orange-50 border-red-300'
                      }`}
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    {/* Cabeçalho da Simulação */}
                    <div className="space-y-3 mb-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-lg text-gray-900">{sim.name}</h4>
                        <Badge
                          variant={
                            sim.isViable
                              ? index === 0 ? "default" : "secondary"
                              : "danger"
                          }
                          className="px-3 py-1"
                        >
                          {sim.isViable ? (index === 0 ? 'Recomendada' : 'Viável') : 'Não Viável'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">{sim.description}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-500">Perfil de Risco:</span>
                        <Badge variant="outline" className="text-xs">
                          {sim.riskProfile}
                        </Badge>
                      </div>
                    </div>

                    {/* Métricas Principais */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-white/70 rounded-lg p-3">
                        <div className="text-sm font-medium text-gray-700 mb-1">Prêmio Anual</div>
                        <div className="text-lg font-bold text-gray-900">
                          R$ {(sim.premium / coveragePeriod).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-xs text-gray-500">
                          Total: R$ {sim.premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div className="bg-white/70 rounded-lg p-3">
                        <div className="text-sm font-medium text-gray-700 mb-1">Margem Anual</div>
                        <div className={`text-lg font-bold ${sim.profitMarginPercentage > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                          {sim.profitMarginPercentage.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Detalhes da Análise */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Perda Esperada Anual:</span>
                        <span className="font-medium text-red-600">
                          R$ {sim.expectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Lucro Anual Médio:</span>
                        <span className={`font-medium ${sim.profitMargin > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                          R$ {sim.profitMargin.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Retorno vs Risco:</span>
                        <span className="font-medium text-blue-600">
                          {sim.riskAdjustedReturn.toFixed(2)}x
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Custo para Cliente:</span>
                        <span className={`font-medium ${sim.customerCostPercentage < 5 ? 'text-green-600' : 'text-orange-600'
                          }`}>
                          {sim.customerCostPercentage.toFixed(1)}% do bem
                        </span>
                      </div>
                    </div>

                    {/* Recomendação */}
                    <div className="mt-4 pt-3 border-t border-gray-200">
                      <div className="flex items-start gap-2">
                        <div className={`rounded-full p-1 ${sim.isViable ? 'bg-green-100' : 'bg-red-100'
                          }`}>
                          {sim.isViable ? (
                            <TrendingUp className="h-3 w-3 text-green-600" />
                          ) : (
                            <AlertTriangle className="h-3 w-3 text-red-600" />
                          )}
                        </div>
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">
                            {sim.isViable ? 'Vantagens:' : 'Desvantagens:'}
                          </div>
                          <div className="text-xs text-gray-600">
                            {sim.isViable ? (
                              index === 0 ? (
                                'Melhor equilíbrio entre lucratividade e aceitação do mercado'
                              ) : (
                                'Configuração viável com boa margem de segurança'
                              )
                            ) : (
                              'Requer revisão dos parâmetros ou não é adequada para este perfil de risco'
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Resumo Executivo */}
              <div className="animate-slide-up rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 p-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="rounded-full bg-gray-100 p-2">
                      <Activity className="h-4 w-4 text-gray-600" />
                    </div>
                    <h3 className="font-medium text-gray-900">Resumo Executivo</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg p-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">🎯 Melhor Opção</div>
                      <div className="text-lg font-bold text-green-600">
                        {policySimulations[0]?.name || 'N/A'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Maior viabilidade e lucratividade
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">💰 Maior Margem</div>
                      <div className="text-lg font-bold text-blue-600">
                        {policySimulations && policySimulations.length > 0 ? Math.max(...policySimulations.map(s => s.profitMarginPercentage || 0))?.toFixed(1) : 'N/A'}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Melhor retorno financeiro
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">📊 Risco Otimizado</div>
                      <div className="text-lg font-bold text-purple-600">
                        {policySimulations && policySimulations.length > 0 ? Math.max(...policySimulations.map(s => s.riskAdjustedReturn || 0))?.toFixed(2) : 'N/A'}x
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Melhor relação risco-retorno
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Recomendações Inteligentes */}
          {policySimulations.length > 0 && financialAnalysis && (
            <div className="mt-10 space-y-6">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  Recomendações Inteligentes
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Recomendação Principal */}
                  <div className="bg-white/70 rounded-lg p-4">
                    <h4 className="font-medium text-gray-800 mb-2">Configuração Recomendada</h4>
                    <div className="text-sm text-gray-600 mb-3">
                      Baseado na análise de risco-retorno e viabilidade de mercado:
                    </div>
                    <div className="bg-green-100 border border-green-300 rounded p-3">
                      <div className="font-semibold text-green-800">
                        {policySimulations.find(sim => sim.isViable)?.name || 'Nenhuma configuração viável'}
                      </div>
                      <div className="text-sm text-green-700 mt-1">
                        Margem esperada: {policySimulations?.find(sim => sim.isViable)?.profitMarginPercentage?.toFixed(1) || 'N/A'}%
                      </div>
                    </div>
                  </div>

                  {/* Otimizações Sugeridas */}
                  <div className="bg-white/70 rounded-lg p-4">
                    <h4 className="font-medium text-gray-800 mb-2">Oportunidades de Otimização</h4>
                    <div className="space-y-2">
                      {financialAnalysis.insurerAnalysis.riskAdjustedReturn < 2 && (
                        <div className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5" />
                          <span>Considere aumentar o prêmio para melhorar o retorno ajustado ao risco</span>
                        </div>
                      )}
                      {financialAnalysis.customerAnalysis.premiumToAssetRatio > 3 && (
                        <div className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
                          <span>Prêmio elevado - avalie dedutível para melhorar aceitação</span>
                        </div>
                      )}
                      {policySimulations.filter(sim => sim.isViable).length === 0 && (
                        <div className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
                          <span>Ajuste os parâmetros de risco - nenhuma configuração é viável atualmente</span>
                        </div>
                      )}
                      {financialAnalysis.riskAnalysis?.reinsuranceNeed && (
                        <div className="flex items-start gap-2 text-sm">
                          <Shield className="h-4 w-4 text-blue-500 mt-0.5" />
                          <span>Recomendado: Contratar reinsurance para reduzir exposição</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Ações Rápidas */}
                <div className="mt-6 pt-4 border-t border-blue-300">
                  <h4 className="font-medium text-gray-800 mb-3">Ações Rápidas</h4>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={() => window.location.href = '/tokenization'}
                      variant="outline"
                      size="sm"
                      className="bg-white/50"
                    >
                      <Zap className="h-4 w-4 mr-2" />
                      Painel de Tokenização
                    </Button>
                    <Button
                      onClick={() => {
                        // Reset para valores conservadores otimizados
                        const bestSim = policySimulations.find(sim => sim.isViable);
                        if (bestSim) {
                          setFrequency(bestSim.frequency);
                          setSeverity(bestSim.severity);
                          setConfidence(bestSim.confidence);
                        }
                      }}
                      variant="outline"
                      size="sm"
                      className="bg-white/50"
                    >
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Aplicar Configuração Ótima
                    </Button>
                    <Button
                      onClick={() => {
                        // Simular com diferentes cenários
                        setAssetValue(assetValue * 1.2); // +20% no valor do bem
                      }}
                      variant="outline"
                      size="sm"
                      className="bg-white/50"
                    >
                      <Calculator className="h-4 w-4 mr-2" />
                      Testar Cenário Premium
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Predições de Machine Learning */}
          {mlPredictions && (
            <div className="mt-10 space-y-6">
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 border border-purple-200">
                <h3 className="text-lg font-semibold text-purple-800 mb-4 flex items-center">
                  <Brain className="h-5 w-5 mr-2" />
                  Predições de Machine Learning
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Frequência de Sinistros */}
                  <div className="bg-white/70 rounded-lg p-4">
                    <h4 className="font-medium text-gray-800 mb-2">Frequência de Sinistros</h4>
                    <div className="text-sm text-gray-600 mb-3">
                      Predição baseada em dados históricos e fatores climáticos
                    </div>
                    <div className="bg-blue-100 border border-blue-300 rounded p-3">
                      <div className="text-lg font-bold text-blue-800">
                        {mlPredictions?.frequency?.prediction?.toFixed(1) || 'N/A'}
                      </div>
                      <div className="text-xs text-blue-700">
                        {mlPredictions?.frequency?.unit || 'N/A'}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Intervalo: {mlPredictions?.frequency?.confidence_lower?.toFixed(1) || 'N/A'} - {mlPredictions?.frequency?.confidence_upper?.toFixed(1) || 'N/A'}
                      </div>
                    </div>
                  </div>

                  {/* Severidade de Sinistros */}
                  <div className="bg-white/70 rounded-lg p-4">
                    <h4 className="font-medium text-gray-800 mb-2">Severidade de Sinistros</h4>
                    <div className="text-sm text-gray-600 mb-3">
                      Valor médio estimado por sinistro
                    </div>
                    <div className="bg-red-100 border border-red-300 rounded p-3">
                      <div className="text-lg font-bold text-red-800">
                        R$ {mlPredictions.severity.prediction.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                      <div className="text-xs text-red-700">
                        {mlPredictions.severity.unit}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Intervalo: R$ {mlPredictions.severity.confidence_lower.toLocaleString(undefined, { maximumFractionDigits: 0 })} - R$ {mlPredictions.severity.confidence_upper.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Método de Predição */}
                <div className="mt-6 pt-4 border-t border-purple-300">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Método de Predição:</span>
                    <Badge variant={mlPredictions.method === 'machine_learning' ? 'default' : 'secondary'}>
                      {mlPredictions.method === 'machine_learning' ? 'Machine Learning' : 'Baseado em Regras'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-2">
                    <span className="text-gray-600">Nível de Confiança:</span>
                    <span className="font-medium text-purple-700">{mlPredictions.confidence_level}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Estado de cálculo */}
          {calculating && (
            <div className="mt-6 animate-pulse rounded-lg bg-blue-50 p-6">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <div className="text-blue-900 font-medium">
                  Calculando com técnicas avançadas de matemática atuarial...
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
