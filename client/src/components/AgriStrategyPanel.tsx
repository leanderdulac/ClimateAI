import { useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, Leaf, Loader2, MapPin, Sprout, TrendingUp } from "lucide-react";

import { buildApiUrl } from "@/lib/api";
import { useLocation } from "@/lib/LocationContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type RiskTolerance = "low" | "medium" | "high";
type StrategyCatalog = {
  supported_crops: string[];
  supported_stages: string[];
  risk_dimensions: string[];
};

type StrategyResponse = {
  climate_outlook: {
    enso?: {
      regime_label?: string;
      regime_confidence?: string;
      reference_date?: string;
      p_el_nino?: number;
      p_la_nina?: number;
      p_neutral?: number;
    };
    enso_observed?: {
      regime_label?: string;
      regime_confidence?: string;
      reference_date?: string;
      p_el_nino?: number;
      p_la_nina?: number;
      p_neutral?: number;
    };
    enso_projected?: {
      regime_label?: string;
      regime_confidence?: string;
      probability?: number;
      p_el_nino?: number;
      p_la_nina?: number;
      p_neutral?: number;
    };
    forecast_source?: string;
  };
  exposure_scores: Record<string, number>;
  operational_actions: Array<{
    horizon: string;
    priority: string;
    category: string;
    action: string;
    rationale: string;
  }>;
  financial_actions: Array<{
    type: string;
    priority: string;
    strategy: string;
    expected_benefit: string;
  }>;
  alert_triggers: Array<{
    name: string;
    condition: string;
    recommended_response: string;
  }>;
};

type QuoteContext = {
  premium: number;
  coveragePeriod: number;
  frequency: number;
  severity: number;
  eventId: string | null;
  status: string | null;
};

type HistoricalContext = {
  days: number;
  totalRainfall: number;
  heavyRainDays: number;
  dryDays: number;
  hotDays: number;
  windyDays: number;
};

const defaultCatalog: StrategyCatalog = {
  supported_crops: ["soybean", "corn", "coffee"],
  supported_stages: ["planning", "planting", "vegetative", "flowering", "grain_fill", "harvest"],
  risk_dimensions: ["heat", "drought", "excess_rain", "flood", "wind", "disease"],
};

export function AgriStrategyPanel() {
  const { selectedLocation, isLoadingLocation } = useLocation();
  const [catalog, setCatalog] = useState<StrategyCatalog>(defaultCatalog);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StrategyResponse | null>(null);
  const [insuranceIntentActive, setInsuranceIntentActive] = useState(false);
  const [quoteContext, setQuoteContext] = useState<QuoteContext | null>(null);
  const [historicalContext, setHistoricalContext] = useState<HistoricalContext | null>(null);
  const loadingStartedAtRef = useRef<number | null>(null);
  const [sessionId] = useState(() => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return `agri-${Date.now()}`;
  });
  const autoPlanRequestedRef = useRef(false);
  const [form, setForm] = useState({
    crop_type: "soybean",
    phenological_stage: "flowering",
    latitude: "",
    longitude: "",
    planning_horizon_days: "120",
    risk_tolerance: "medium" as RiskTolerance,
    productive_farm: true,
  });

  useEffect(() => {
    void (async () => {
      setLoadingCatalog(true);
      try {
        const response = await fetch(buildApiUrl('/api/v1/agri-strategy/catalog'));
        if (!response.ok) {
          throw new Error('Não foi possível carregar o catálogo agroclimático.');
        }
        const data = await response.json() as StrategyCatalog;
        setCatalog(data);
        setForm((current) => ({
          ...current,
          crop_type: data.supported_crops[0] || current.crop_type,
          phenological_stage: data.supported_stages.includes(current.phenological_stage)
            ? current.phenological_stage
            : (data.supported_stages[0] || current.phenological_stage),
        }));
      } catch (catalogError) {
        console.warn(catalogError);
      } finally {
        setLoadingCatalog(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedLocation) {
      return;
    }

    autoPlanRequestedRef.current = false;

    setForm((current) => ({
      ...current,
      latitude: selectedLocation.latitude.toFixed(4),
      longitude: selectedLocation.longitude.toFixed(4),
    }));
  }, [selectedLocation]);

  useEffect(() => {
    const persistJourneyEvent = async (
      eventType: string,
      metadata?: Record<string, unknown>,
    ) => {
      try {
        await fetch(buildApiUrl('/api/v1/agri-strategy/journey/event'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            event_type: eventType,
            location: selectedLocation
              ? {
                latitude: selectedLocation.latitude,
                longitude: selectedLocation.longitude,
                city: selectedLocation.cidade,
                state: selectedLocation.estado,
              }
              : undefined,
            quote_context: quoteContext
              ? {
                premium: quoteContext.premium,
                coverage_period: quoteContext.coveragePeriod,
                frequency: quoteContext.frequency,
                severity: quoteContext.severity,
                event_id: quoteContext.eventId,
                status: quoteContext.status,
              }
              : undefined,
            historical_context: historicalContext
              ? {
                days: historicalContext.days,
                total_rainfall: historicalContext.totalRainfall,
                heavy_rain_days: historicalContext.heavyRainDays,
                dry_days: historicalContext.dryDays,
                hot_days: historicalContext.hotDays,
                windy_days: historicalContext.windyDays,
              }
              : undefined,
            metadata: metadata || {},
          }),
        });
      } catch (journeyError) {
        console.warn('Falha ao persistir evento de jornada', journeyError);
      }
    };

    const onInsuranceIntent = (event: Event) => {
      const customEvent = event as CustomEvent<{ active?: boolean }>;
      const intentActive = customEvent.detail?.active !== false;
      setInsuranceIntentActive(intentActive);
      if (intentActive) {
        autoPlanRequestedRef.current = false;
      }
      void persistJourneyEvent('insurance_intent', {
        source: (customEvent as CustomEvent<{ source?: string }>).detail?.source || 'unknown',
      });
    };

    const onQuoteCalculated = (
      event: Event,
    ) => {
      const customEvent = event as CustomEvent<QuoteContext>;
      if (customEvent.detail) {
        setInsuranceIntentActive(true);
        setQuoteContext(customEvent.detail);
        autoPlanRequestedRef.current = false;
        void persistJourneyEvent('quote_calculated', {
          source: 'pricing-simulator',
        });
      }
    };

    const onHistoricalContext = (event: Event) => {
      const customEvent = event as CustomEvent<HistoricalContext>;
      if (customEvent.detail) {
        setHistoricalContext(customEvent.detail);
        void persistJourneyEvent('historical_context_loaded', {
          source: 'insurance-recommendation',
        });
      }
    };

    window.addEventListener('climateai:insurance-intent', onInsuranceIntent as EventListener);
    window.addEventListener('climateai:quote-calculated', onQuoteCalculated as EventListener);
    window.addEventListener('climateai:historical-context', onHistoricalContext as EventListener);

    return () => {
      window.removeEventListener('climateai:insurance-intent', onInsuranceIntent as EventListener);
      window.removeEventListener('climateai:quote-calculated', onQuoteCalculated as EventListener);
      window.removeEventListener('climateai:historical-context', onHistoricalContext as EventListener);
    };
  }, [historicalContext, quoteContext, selectedLocation, sessionId]);

  const handleGeneratePlan = async () => {
    if (!selectedLocation) {
      setError('Selecione uma localização para gerar a estratégia agroclimática.');
      return;
    }

    if (!insuranceIntentActive) {
      setError('Ative uma simulação de seguro climático para gerar a estratégia da cotação.');
      return;
    }

    setLoadingPlan(true);
    loadingStartedAtRef.current = Date.now();
    setError(null);

    try {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 15000);

      const response = await fetch(buildApiUrl('/api/v1/agri-strategy/plan'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        body: JSON.stringify({
          crop_type: form.crop_type,
          phenological_stage: form.phenological_stage,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          planning_horizon_days: Number(form.planning_horizon_days),
          risk_tolerance: form.risk_tolerance,
          session_id: sessionId,
          quote_context: quoteContext
            ? {
              premium: quoteContext.premium,
              coverage_period: quoteContext.coveragePeriod,
              frequency: quoteContext.frequency,
              severity: quoteContext.severity,
              event_id: quoteContext.eventId,
              status: quoteContext.status,
            }
            : undefined,
          historical_context: historicalContext
            ? {
              days: historicalContext.days,
              total_rainfall: historicalContext.totalRainfall,
              heavy_rain_days: historicalContext.heavyRainDays,
              dry_days: historicalContext.dryDays,
              hot_days: historicalContext.hotDays,
              windy_days: historicalContext.windyDays,
            }
            : undefined,
          farm_profile: {
            productive_farm: form.productive_farm,
            irrigation_available: false,
            drainage_level: 'medium',
            soil_cover_level: 'medium',
          },
        }),
      });

      window.clearTimeout(timeoutId);

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'Falha ao gerar o plano agroclimático.');
      }

      setResult(await response.json() as StrategyResponse);
    } catch (planError) {
      if (planError instanceof DOMException && planError.name === 'AbortError') {
        setError('A geração da estratégia demorou demais. Tente novamente em alguns segundos.');
      } else {
        setError(planError instanceof Error ? planError.message : 'Falha ao gerar o plano agroclimático.');
      }
      setResult(null);
    } finally {
      setLoadingPlan(false);
      loadingStartedAtRef.current = null;
    }
  };

  useEffect(() => {
    if (!loadingPlan) {
      return;
    }

    const watchdogId = window.setTimeout(() => {
      if (!loadingStartedAtRef.current) {
        return;
      }

      const elapsedMs = Date.now() - loadingStartedAtRef.current;
      if (elapsedMs >= 20000) {
        setLoadingPlan(false);
        loadingStartedAtRef.current = null;
        setError('A geração da estratégia excedeu o tempo limite. Tente novamente.');
      }
    }, 20000);

    return () => window.clearTimeout(watchdogId);
  }, [loadingPlan]);

  useEffect(() => {
    const canAutoGenerate = Boolean(
      selectedLocation &&
      insuranceIntentActive &&
      !isLoadingLocation &&
      quoteContext &&
      !loadingPlan,
    );

    if (!canAutoGenerate || autoPlanRequestedRef.current) {
      return;
    }

    autoPlanRequestedRef.current = true;
    void handleGeneratePlan();
  }, [insuranceIntentActive, isLoadingLocation, loadingPlan, quoteContext, selectedLocation]);

  const riskLabelByKey = useMemo(() => ({
    heat: 'calor extremo',
    drought: 'seca',
    excess_rain: 'chuva excessiva',
    flood: 'alagamento',
    wind: 'vento forte',
    disease: 'doenças',
  }), []);

  const topRisks = Object.entries(result?.exposure_scores || {})
    .sort(([, left], [, right]) => right - left)
    .slice(0, 3);

  const ensoObserved = result?.climate_outlook.enso_observed || result?.climate_outlook.enso;
  const ensoProjected = result?.climate_outlook.enso_projected;

  return (
    <Card className="border-none shadow-soft-xl bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Leaf className="h-6 w-6 text-emerald-500" />
              Estratégia Agroclimática
            </CardTitle>
            <CardDescription className="mt-2 max-w-2xl text-sm leading-relaxed">
              Gera um plano operacional e financeiro integrado à cotação de seguro, com base em ENSO, previsão NOAA e perfil da lavoura.
            </CardDescription>
          </div>
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600">
            {loadingCatalog ? 'Atualizando catálogo...' : 'ENSO + NOAA'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-8">
        <div className="rounded-xl border border-border/60 bg-muted/20 p-4 text-sm">
          <div className="flex flex-wrap items-center gap-2 text-foreground">
            <MapPin className="h-4 w-4 text-primary" />
            <span className="font-medium">Região da cotação:</span>
            <span>
              {selectedLocation?.cidade && selectedLocation?.estado
                ? `${selectedLocation.cidade}, ${selectedLocation.estado}`
                : 'não selecionada'}
            </span>
            {selectedLocation && (
              <Badge variant="secondary">
                {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
              </Badge>
            )}
          </div>
          <div className="mt-2 text-muted-foreground">
            {insuranceIntentActive
              ? 'Intenção de contratação de seguro climático detectada na jornada.'
              : 'Este módulo é ativado automaticamente quando o cliente inicia a simulação de seguro climático.'}
          </div>
          {quoteContext && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-foreground">
              <span className="font-medium">Cotação atual:</span>
              <Badge variant="outline">Prêmio: R$ {quoteContext.premium.toLocaleString(undefined, { maximumFractionDigits: 2 })}</Badge>
              <Badge variant="outline">Período: {quoteContext.coveragePeriod} ano(s)</Badge>
              <Badge variant="outline">Frequência: {quoteContext.frequency}%</Badge>
              {quoteContext.eventId && <Badge variant="outline">Evento: {quoteContext.eventId}</Badge>}
            </div>
          )}
          {historicalContext && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-foreground">
              <span className="font-medium">Histórico climático carregado:</span>
              <Badge variant="outline">Dias analisados: {historicalContext.days}</Badge>
              <Badge variant="outline">Dias secos: {historicalContext.dryDays}</Badge>
              <Badge variant="outline">Chuva forte: {historicalContext.heavyRainDays}</Badge>
              <Badge variant="outline">Dias quentes: {historicalContext.hotDays}</Badge>
            </div>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="agri-crop">Cultura</Label>
            <Select value={form.crop_type} onValueChange={(value) => setForm((current) => ({ ...current, crop_type: value }))}>
              <SelectTrigger id="agri-crop">
                <SelectValue placeholder="Selecione a cultura" />
              </SelectTrigger>
              <SelectContent>
                {catalog.supported_crops.map((crop) => (
                  <SelectItem key={crop} value={crop}>{crop}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-stage">Estágio fenológico</Label>
            <Select value={form.phenological_stage} onValueChange={(value) => setForm((current) => ({ ...current, phenological_stage: value }))}>
              <SelectTrigger id="agri-stage">
                <SelectValue placeholder="Selecione o estágio" />
              </SelectTrigger>
              <SelectContent>
                {catalog.supported_stages.map((stage) => (
                  <SelectItem key={stage} value={stage}>{stage}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-risk">Tolerância ao risco</Label>
            <Select value={form.risk_tolerance} onValueChange={(value: RiskTolerance) => setForm((current) => ({ ...current, risk_tolerance: value }))}>
              <SelectTrigger id="agri-risk">
                <SelectValue placeholder="Selecione a tolerância" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Baixa</SelectItem>
                <SelectItem value="medium">Média</SelectItem>
                <SelectItem value="high">Alta</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-lat">Latitude</Label>
            <Input
              id="agri-lat"
              value={form.latitude}
              readOnly={Boolean(selectedLocation)}
              onChange={(event) => setForm((current) => ({ ...current, latitude: event.target.value }))}
              placeholder={selectedLocation ? 'Preenchida automaticamente pela localização' : 'Informe a latitude'}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-lon">Longitude</Label>
            <Input
              id="agri-lon"
              value={form.longitude}
              readOnly={Boolean(selectedLocation)}
              onChange={(event) => setForm((current) => ({ ...current, longitude: event.target.value }))}
              placeholder={selectedLocation ? 'Preenchida automaticamente pela localização' : 'Informe a longitude'}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-horizon">Horizonte de planejamento (dias)</Label>
            <Input id="agri-horizon" value={form.planning_horizon_days} onChange={(event) => setForm((current) => ({ ...current, planning_horizon_days: event.target.value }))} />
          </div>

          <div className="space-y-2 md:col-span-2 xl:col-span-3">
            <label htmlFor="agri-productive-farm" className="flex items-center gap-3 text-sm font-medium text-foreground">
              <input
                id="agri-productive-farm"
                type="checkbox"
                checked={form.productive_farm}
                onChange={(event) => setForm((current) => ({ ...current, productive_farm: event.target.checked }))}
                className="h-4 w-4 rounded border-input"
              />
              Fazenda produtiva (área em produção ativa)
            </label>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            onClick={handleGeneratePlan}
            disabled={loadingPlan || !selectedLocation || !insuranceIntentActive}
            className="min-w-52"
          >
            {loadingPlan ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sprout className="mr-2 h-4 w-4" />}
            Gerar estratégia da cotação
          </Button>
          <div className="text-sm text-muted-foreground">
            Riscos monitorados: {catalog.risk_dimensions.map((risk) => riskLabelByKey[risk as keyof typeof riskLabelByKey] || risk).join(', ')}
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      ENSO observado
                    </div>
                    <div className="text-xl font-semibold capitalize text-foreground">
                      {(ensoObserved?.regime_label || 'indefinido').replace('_', ' ')}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Confiança {ensoObserved?.regime_confidence || 'n/a'}
                    </div>
                    {typeof ensoObserved?.p_el_nino === 'number' && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        El Nino {Math.round((ensoObserved.p_el_nino || 0) * 100)}% | La Nina {Math.round((ensoObserved.p_la_nina || 0) * 100)}%
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      ENSO projetado
                    </div>
                    <div className="text-xl font-semibold capitalize text-foreground">
                      {(ensoProjected?.regime_label || 'indefinido').replace('_', ' ')}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Confiança {ensoProjected?.regime_confidence || 'n/a'}
                    </div>
                    {typeof ensoProjected?.probability === 'number' && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        Probabilidade: {Math.round(ensoProjected.probability * 100)}%
                      </div>
                    )}
                    {typeof ensoProjected?.p_el_nino === 'number' && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        El Nino {Math.round((ensoProjected.p_el_nino || 0) * 100)}% | La Nina {Math.round((ensoProjected.p_la_nina || 0) * 100)}%
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      Forecast
                    </div>
                    <div className="text-xl font-semibold text-foreground">
                      {result.climate_outlook.forecast_source || 'NOAA/NWS'}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Ref. {ensoObserved?.reference_date || 'ao vivo'}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <Leaf className="h-4 w-4" />
                      Maiores exposições
                    </div>
                    <div className="space-y-1 text-sm text-foreground">
                      {topRisks.map(([risk, score]) => (
                        <div key={risk} className="flex items-center justify-between gap-3">
                          <span className="capitalize">{riskLabelByKey[risk as keyof typeof riskLabelByKey] || risk.replace('_', ' ')}</span>
                          <Badge variant="secondary">{Math.round(score * 100)}%</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="border border-border/60 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-lg">Ações operacionais</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.operational_actions.slice(0, 4).map((action) => (
                    <div key={`${action.horizon}-${action.category}-${action.action}`} className="rounded-xl border border-border/60 p-4">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge>{action.priority}</Badge>
                        <Badge variant="outline">{action.horizon}</Badge>
                        <span className="text-sm font-medium capitalize text-muted-foreground">{action.category.replace('_', ' ')}</span>
                      </div>
                      <div className="font-medium text-foreground">{action.action}</div>
                      <p className="mt-2 text-sm text-muted-foreground">{action.rationale}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card className="border border-border/60 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-lg">Ações financeiras</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.financial_actions.slice(0, 3).map((action) => (
                    <div key={`${action.type}-${action.strategy}`} className="rounded-xl border border-border/60 p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <Badge>{action.priority}</Badge>
                        <span className="text-sm font-medium capitalize text-muted-foreground">{action.type.replace('_', ' ')}</span>
                      </div>
                      <div className="font-medium text-foreground">{action.strategy}</div>
                      <p className="mt-2 text-sm text-muted-foreground">{action.expected_benefit}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="border border-border/60 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-lg">Gatilhos de alerta</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.alert_triggers.slice(0, 3).map((trigger) => (
                    <div key={trigger.name} className="rounded-xl border border-border/60 p-4">
                      <div className="font-medium text-foreground">{trigger.name}</div>
                      <p className="mt-2 text-sm text-muted-foreground">{trigger.condition}</p>
                      <p className="mt-2 text-sm text-foreground">{trigger.recommended_response}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}