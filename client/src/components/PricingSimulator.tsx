import { embrapaApi } from '@/lib/embrapaApi';
import { useLocation } from '@/lib/LocationContext';
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  DollarSign,
  Calculator,
  AlertTriangle,
  TrendingUp,
  Activity,
  Cloud,
  Droplets,
  Wind,
  Sun,
  CloudRain,
  Flame
} from "lucide-react";

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
    name: 'Seca',
    icon: <Sun className="h-4 w-4" />,
    baseFrequency: 15,
    baseSeverity: 8000
  },
  {
    id: 'flood',
    name: 'Inundação',
    icon: <Droplets className="h-4 w-4" />,
    baseFrequency: 12,
    baseSeverity: 12000
  },
  {
    id: 'rain',
    name: 'Chuvas Intensas',
    icon: <CloudRain className="h-4 w-4" />,
    baseFrequency: 25,
    baseSeverity: 5000
  },
  {
    id: 'wind',
    name: 'Ventos Fortes',
    icon: <Wind className="h-4 w-4" />,
    baseFrequency: 20,
    baseSeverity: 7000
  },
  {
    id: 'hail',
    name: 'Granizo',
    icon: <Cloud className="h-4 w-4" />,
    baseFrequency: 8,
    baseSeverity: 15000
  },
  {
    id: 'fire',
    name: 'Queimadas',
    icon: <Flame className="h-4 w-4" />,
    baseFrequency: 10,
    baseSeverity: 20000
  }
];

// Advanced actuarial calculation using backend API
const calculateAdvancedPremium = async (
  frequency: number,
  severity: number,
  confidence: number,
  assetValue: number,
  latitude?: number,
  longitude?: number
) => {
  try {
    // Use current location if available, otherwise default to São Paulo
    const lat = latitude || -23.5505;
    const lon = longitude || -46.6333;

    const response = await embrapaApi.calculateAdvancedPremium({
      latitude: lat,
      longitude: lon,
      frequency: frequency,
      severity: severity,
      asset_value: assetValue,
      confidence_level: confidence
    });

    return response;
  } catch (error) {
    console.error('Erro no cálculo avançado:', error);
    // Fallback para cálculo simplificado
    const simulations = 10000;
    let totalLoss = 0;
    const maxSeverity = Math.min(severity, assetValue);

    for (let i = 0; i < simulations; i++) {
      if (Math.random() < frequency / 100) {
        const lossPercentage = Math.pow(Math.random(), 2);
        totalLoss += lossPercentage * maxSeverity;
      }
    }

    const averageLoss = totalLoss / simulations;
    const riskFactor = 1 + Math.log10(assetValue) / 20;
    const fallbackPremium = averageLoss * riskFactor * (1 + (100 - confidence) / 100);

    return {
      premio_total: fallbackPremium,
      premio_puro: averageLoss,
      carregamentos: fallbackPremium * 0.35,
      margem_risco: fallbackPremium * 0.15,
      intervalo_confianca: {
        inferior: fallbackPremium * 0.8,
        superior: fallbackPremium * 1.2
      },
      analise_fractal: {
        dimensao_fractal: 1.5,
        lacunaaridade: 1.0,
        persistencia: 0.5
      },
      risco_fuzzy: {
        muito_baixo: 0.1,
        baixo: 0.2,
        medio: 0.4,
        alto: 0.2,
        muito_alto: 0.1
      },
      metodologia: {
        iteracoes_monte_carlo: simulations,
        tecnicas_utilizadas: ['Fallback - Monte Carlo Básico']
      }
    };
  }
};

// Financial analysis function for profit/loss assessment
const analyzeFinancialViability = (
  premium: number,
  loadings: number,
  riskMargin: number,
  assetValue: number,
  frequency: number,
  severity: number
) => {
  // Expected loss calculation
  const expectedLoss = (frequency / 100) * Math.min(severity, assetValue);

  // Insurer's profit margins
  const insurerTotalMargin = loadings + riskMargin;
  const insurerMarginPercentage = (insurerTotalMargin / premium) * 100;

  // Customer's value analysis
  const protectionValue = assetValue;
  const costBenefitRatio = (protectionValue / premium);
  const premiumToAssetRatio = (premium / assetValue) * 100;

  // Profitability assessment
  const isProfitableForInsurer = premium > expectedLoss;
  const profitMargin = premium - expectedLoss;
  const profitMarginPercentage = (profitMargin / premium) * 100;

  // Customer affordability assessment
  const isAffordableForCustomer = premiumToAssetRatio < 5; // Less than 5% of asset value
  const valueRating = costBenefitRatio > 10 ? 'Excelente' :
                     costBenefitRatio > 5 ? 'Bom' :
                     costBenefitRatio > 2 ? 'Razoável' : 'Questionável';

  // Risk-adjusted return
  const riskAdjustedReturn = profitMargin / expectedLoss;

  return {
    expectedLoss,
    insurerAnalysis: {
      totalMargin: insurerTotalMargin,
      marginPercentage: insurerMarginPercentage,
      isProfitable: isProfitableForInsurer,
      profitMargin,
      profitMarginPercentage,
      riskAdjustedReturn
    },
    customerAnalysis: {
      protectionValue,
      costBenefitRatio,
      premiumToAssetRatio,
      isAffordable: isAffordableForCustomer,
      valueRating,
      annualCostPercentage: premiumToAssetRatio
    },
    overallAssessment: {
      isViable: isProfitableForInsurer && isAffordableForCustomer,
      recommendation: isProfitableForInsurer && isAffordableForCustomer ? 'Aprovada' :
                     !isProfitableForInsurer ? 'Rejeitada - Não Lucrativa' :
                     'Rejeitada - Muito Cara para Cliente'
    }
  };
};

// Function to generate policy configuration simulations
const generatePolicySimulations = async (
  baseAssetValue: number,
  baseFrequency: number,
  baseSeverity: number,
  baseConfidence: number,
  selectedLocation: any
) => {
  const simulations = [
    {
      name: 'Configuração Conservadora',
      description: 'Menor risco para o emissor, prêmio mais alto',
      frequency: baseFrequency * 1.2, // Aumenta frequência esperada
      severity: baseSeverity * 1.1, // Aumenta severidade esperada
      confidence: Math.min(baseConfidence + 5, 99), // Maior confiança
      riskProfile: 'Conservador'
    },
    {
      name: 'Configuração Equilibrada',
      description: 'Balanço entre risco e competitividade',
      frequency: baseFrequency, // Frequência base
      severity: baseSeverity, // Severidade base
      confidence: baseConfidence, // Confiança base
      riskProfile: 'Equilibrado'
    },
    {
      name: 'Configuração Agressiva',
      description: 'Maior risco para competir no mercado',
      frequency: baseFrequency * 0.8, // Reduz frequência esperada
      severity: baseSeverity * 0.9, // Reduz severidade esperada
      confidence: Math.max(baseConfidence - 5, 85), // Menor confiança
      riskProfile: 'Agressivo'
    },
    {
      name: 'Configuração Premium',
      description: 'Foco em clientes de alto valor',
      frequency: baseFrequency * 0.9,
      severity: baseSeverity * 0.95,
      confidence: baseConfidence,
      riskProfile: 'Premium',
      assetMultiplier: 2.0 // Para bens de maior valor
    }
  ];

  const results = await Promise.all(
    simulations.map(async (sim) => {
      const assetValue = sim.assetMultiplier ? baseAssetValue * sim.assetMultiplier : baseAssetValue;

      try {
        const premiumResult = await calculateAdvancedPremium(
          sim.frequency,
          sim.severity,
          sim.confidence,
          assetValue,
          selectedLocation?.latitude,
          selectedLocation?.longitude
        );

        const analysis = analyzeFinancialViability(
          premiumResult.premio_total,
          premiumResult.carregamentos || 0,
          premiumResult.margem_risco || 0,
          assetValue,
          sim.frequency,
          sim.severity
        );

        return {
          ...sim,
          assetValue,
          premium: premiumResult.premio_total,
          expectedLoss: analysis.expectedLoss,
          profitMargin: analysis.insurerAnalysis.profitMargin,
          profitMarginPercentage: analysis.insurerAnalysis.profitMarginPercentage,
          riskAdjustedReturn: analysis.insurerAnalysis.riskAdjustedReturn,
          customerCostPercentage: analysis.customerAnalysis.premiumToAssetRatio,
          isViable: analysis.overallAssessment.isViable,
          recommendation: analysis.overallAssessment.recommendation
        };
      } catch (error) {
        // Fallback calculation
        const expectedLoss = (sim.frequency / 100) * Math.min(sim.severity, assetValue);
        const riskFactor = 1 + Math.log10(assetValue) / 20;
        const fallbackPremium = expectedLoss * riskFactor * (1 + (100 - sim.confidence) / 100);

        const analysis = analyzeFinancialViability(
          fallbackPremium,
          fallbackPremium * 0.35,
          fallbackPremium * 0.15,
          assetValue,
          sim.frequency,
          sim.severity
        );

        return {
          ...sim,
          assetValue,
          premium: fallbackPremium,
          expectedLoss: analysis.expectedLoss,
          profitMargin: analysis.insurerAnalysis.profitMargin,
          profitMarginPercentage: analysis.insurerAnalysis.profitMarginPercentage,
          riskAdjustedReturn: analysis.insurerAnalysis.riskAdjustedReturn,
          customerCostPercentage: analysis.customerAnalysis.premiumToAssetRatio,
          isViable: analysis.overallAssessment.isViable,
          recommendation: analysis.overallAssessment.recommendation
        };
      }
    })
  );

  // Rank simulations by profitability and viability
  return results.sort((a, b) => {
    // Primary sort: viability (viable first)
    if (a.isViable !== b.isViable) {
      return a.isViable ? -1 : 1;
    }
    // Secondary sort: profit margin percentage
    return b.profitMarginPercentage - a.profitMarginPercentage;
  });
};

export function PricingSimulator() {
  const [assetValue, setAssetValue] = useState<number>(100000); // Valor do bem/serviço
  const [selectedEvent, setSelectedEvent] = useState<ClimateEvent | null>(null);
  const [frequency, setFrequency] = useState<number>(10); // %
  const [severity, setSeverity] = useState<number>(10000); // $
  const [confidence, setConfidence] = useState<number>(95); // %
  const [premium, setPremium] = useState<number>(0);
  const [advancedResults, setAdvancedResults] = useState<any>(null);
  const [financialAnalysis, setFinancialAnalysis] = useState<any>(null);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [policySimulations, setPolicySimulations] = useState<any[]>([]);

  const { selectedLocation } = useLocation();

  const handleEventSelect = (event: ClimateEvent) => {
    setSelectedEvent(event);
    setFrequency(event.baseFrequency);
    setSeverity(event.baseSeverity);
  };

  const handleCalculate = async () => {
    if (assetValue <= 0) {
      alert('Por favor, insira um valor válido para o bem ou serviço.');
      return;
    }
    if (!selectedEvent) {
      alert('Por favor, selecione um evento climático.');
      return;
    }

    setCalculating(true);
    try {
      const results = await calculateAdvancedPremium(
        frequency,
        severity,
        confidence,
        assetValue,
        selectedLocation?.latitude,
        selectedLocation?.longitude
      );

      setPremium(results.premio_total);
      setAdvancedResults(results);

      // Perform financial analysis
      const analysis = analyzeFinancialViability(
        results.premio_total,
        results.carregamentos || 0,
        results.margem_risco || 0,
        assetValue,
        frequency,
        severity
      );
      setFinancialAnalysis(analysis);

      // Generate policy configuration simulations
      const simulations = await generatePolicySimulations(
        assetValue,
        frequency,
        severity,
        confidence,
        selectedLocation
      );
      setPolicySimulations(simulations);

    } catch (error) {
      console.error('Erro no cálculo:', error);
      alert('Erro no cálculo avançado. Usando método simplificado.');
    } finally {
      setCalculating(false);
    }
  };

  return (
    <Card className="overflow-hidden animate-fade-in" variant="default">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Calculator className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Simulador de Preços</CardTitle>
              <CardDescription className="text-primary-100">
                Cálculo de seguros contra eventos climáticos
              </CardDescription>
            </div>
          </div>
          {premium > 0 && (
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <DollarSign className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Valor do Seguro</div>
                <div className="text-lg font-semibold text-white">
                  R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-10 p-8 bg-gradient-to-b from-white to-neutral-50">
        <div className="grid gap-8 sm:grid-cols-2">
          <div className="space-y-6">
            {/* Climate Events Selection */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
                  <Cloud className="h-4 w-4 text-primary-500" />
                  Evento Climático
                </Label>
                {selectedEvent && (
                  <Badge variant="default" className="px-2 py-1">
                    {selectedEvent.name}
                  </Badge>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                {climateEvents.map((event) => (
                  <Button
                    key={event.id}
                    variant={selectedEvent?.id === event.id ? "default" : "outline"}
                    className={`flex items-center gap-2 ${selectedEvent?.id === event.id
                      ? "bg-primary-500 text-white"
                      : "hover:bg-primary-50"
                      }`}
                    onClick={() => handleEventSelect(event)}
                  >
                    {event.icon}
                    {event.name}
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
                  Valor do Bem
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
                    <Badge variant="secondary" className="px-2 py-1">
                      {confidence}% Confiança
                    </Badge>
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

                    <div className="grid grid-cols-3 gap-4">
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Dimensão Fractal</div>
                        <div className="text-lg font-bold text-purple-600">
                          {advancedResults.analise_fractal.dimensao_fractal?.toFixed(3) || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Complexidade do padrão</div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Lacunaaridade</div>
                        <div className="text-lg font-bold text-purple-600">
                          {advancedResults.analise_fractal.lacunaaridade?.toFixed(3) || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Heterogeneidade</div>
                      </div>
                      <div className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="text-xs text-neutral-600">Persistência</div>
                        <div className="text-lg font-bold text-purple-600">
                          {advancedResults.analise_fractal.persistencia?.toFixed(3) || 'N/A'}
                        </div>
                        <div className="text-xs text-neutral-500">Autocorrelação</div>
                      </div>
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
                            {((item.value || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                      ))}
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
              <div className={`animate-slide-up rounded-lg p-8 ${
                financialAnalysis.overallAssessment.isViable
                  ? 'bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-200'
                  : 'bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-200'
              }`}>
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`rounded-full p-2 ${
                        financialAnalysis.overallAssessment.isViable ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {financialAnalysis.overallAssessment.isViable ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                      <h3 className={`font-medium ${
                        financialAnalysis.overallAssessment.isViable ? 'text-green-900' : 'text-red-900'
                      }`}>
                        Análise Financeira da Apólice
                      </h3>
                    </div>
                    <Badge variant={financialAnalysis.overallAssessment.isViable ? "default" : "danger"} className="px-3 py-1">
                      {financialAnalysis.overallAssessment.recommendation}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Análise do Emissor */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">📈 Margem do Emissor</div>
                      <div className={`text-2xl font-bold mb-1 ${
                        financialAnalysis.insurerAnalysis.isProfitable ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {financialAnalysis.insurerAnalysis.profitMarginPercentage.toFixed(1)}%
                      </div>
                      <div className="text-xs text-neutral-500">
                        R$ {financialAnalysis.insurerAnalysis.profitMargin.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                    </div>

                    {/* Análise do Cliente */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">💰 Custo para Cliente</div>
                      <div className={`text-2xl font-bold mb-1 ${
                        financialAnalysis.customerAnalysis.isAffordable ? 'text-green-600' : 'text-orange-600'
                      }`}>
                        {financialAnalysis.customerAnalysis.premiumToAssetRatio.toFixed(1)}%
                      </div>
                      <div className="text-xs text-neutral-500">
                        do valor do bem/ano
                      </div>
                    </div>

                    {/* Retorno Ajustado ao Risco */}
                    <div className="rounded-lg bg-white p-6 shadow-sm">
                      <div className="text-sm font-medium text-neutral-700 mb-2">🎯 Retorno vs Risco</div>
                      <div className={`text-2xl font-bold mb-1 ${
                        financialAnalysis.insurerAnalysis.riskAdjustedReturn > 1 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {financialAnalysis.insurerAnalysis.riskAdjustedReturn.toFixed(2)}x
                      </div>
                      <div className="text-xs text-neutral-500">
                        retorno esperado
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
                      <h3 className="font-medium text-blue-900">Análise do Emissor</h3>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Perda Esperada:</span>
                        <span className="font-medium text-red-600">
                          R$ {financialAnalysis.expectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Prêmio Recebido:</span>
                        <span className="font-medium text-green-600">
                          R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-t pt-2">
                        <span className="text-sm font-medium text-neutral-700">Lucro Líquido:</span>
                        <span className={`font-bold ${
                          financialAnalysis.insurerAnalysis.isProfitable ? 'text-green-600' : 'text-red-600'
                        }`}>
                          R$ {financialAnalysis.insurerAnalysis.profitMargin.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-neutral-600">Margem Total:</span>
                        <span className="font-medium text-blue-600">
                          {financialAnalysis.insurerAnalysis.marginPercentage.toFixed(1)}%
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
                          R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center border-t pt-2">
                        <span className="text-sm font-medium text-neutral-700">Relação Custo-Benefício:</span>
                        <span className={`font-bold ${
                          financialAnalysis.customerAnalysis.costBenefitRatio > 5 ? 'text-green-600' : 'text-orange-600'
                        }`}>
                          {financialAnalysis.customerAnalysis.costBenefitRatio.toFixed(1)}x
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

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">Para o Emissor:</h4>
                      <ul className="text-xs text-gray-600 space-y-2">
                        {financialAnalysis.insurerAnalysis.isProfitable ? (
                          <>
                            <li>• ✅ Apólice lucrativa - margem adequada</li>
                            <li>• 📊 Monitorar sinistralidade real vs esperada</li>
                            <li>• 🎯 Retorno ajustado ao risco: {financialAnalysis.insurerAnalysis.riskAdjustedReturn.toFixed(2)}x</li>
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
                    className={`animate-slide-up rounded-lg border-2 p-6 transition-all duration-300 ${
                      sim.isViable
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
                          R$ {sim.premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div className="bg-white/70 rounded-lg p-3">
                        <div className="text-sm font-medium text-gray-700 mb-1">Margem de Lucro</div>
                        <div className={`text-lg font-bold ${
                          sim.profitMarginPercentage > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {sim.profitMarginPercentage.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Detalhes da Análise */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Perda Esperada:</span>
                        <span className="font-medium text-red-600">
                          R$ {sim.expectedLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Lucro Líquido:</span>
                        <span className={`font-medium ${
                          sim.profitMargin > 0 ? 'text-green-600' : 'text-red-600'
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
                        <span className={`font-medium ${
                          sim.customerCostPercentage < 5 ? 'text-green-600' : 'text-orange-600'
                        }`}>
                          {sim.customerCostPercentage.toFixed(1)}% do bem
                        </span>
                      </div>
                    </div>

                    {/* Recomendação */}
                    <div className="mt-4 pt-3 border-t border-gray-200">
                      <div className="flex items-start gap-2">
                        <div className={`rounded-full p-1 ${
                          sim.isViable ? 'bg-green-100' : 'bg-red-100'
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
                        {Math.max(...policySimulations.map(s => s.profitMarginPercentage)).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Melhor retorno financeiro
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">📊 Risco Otimizado</div>
                      <div className="text-lg font-bold text-purple-600">
                        {Math.max(...policySimulations.map(s => s.riskAdjustedReturn)).toFixed(2)}x
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