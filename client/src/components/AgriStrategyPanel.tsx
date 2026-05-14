import { useEffect, useState } from "react";
import { AlertCircle, Leaf, Loader2, MapPin, Sprout, TrendingUp } from "lucide-react";

import { buildApiUrl } from "@/lib/api";
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

const defaultCatalog: StrategyCatalog = {
  supported_crops: ["soybean", "corn", "coffee"],
  supported_stages: ["planning", "planting", "vegetative", "flowering", "grain_fill", "harvest"],
  risk_dimensions: ["heat", "drought", "excess_rain", "flood", "wind", "disease"],
};

export function AgriStrategyPanel() {
  const [catalog, setCatalog] = useState<StrategyCatalog>(defaultCatalog);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StrategyResponse | null>(null);
  const [form, setForm] = useState({
    crop_type: "soybean",
    phenological_stage: "flowering",
    latitude: "-23.55",
    longitude: "-46.63",
    planning_horizon_days: "120",
    risk_tolerance: "medium" as RiskTolerance,
  });

  useEffect(() => {
    void (async () => {
      setLoadingCatalog(true);
      try {
        const response = await fetch(buildApiUrl('/api/v1/agri-strategy/catalog'));
        if (!response.ok) {
          throw new Error('Nao foi possivel carregar o catalogo agro.');
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

  const handleGeneratePlan = async () => {
    setLoadingPlan(true);
    setError(null);

    try {
      const response = await fetch(buildApiUrl('/api/v1/agri-strategy/plan'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          crop_type: form.crop_type,
          phenological_stage: form.phenological_stage,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          planning_horizon_days: Number(form.planning_horizon_days),
          risk_tolerance: form.risk_tolerance,
          farm_profile: {
            irrigation_available: false,
            drainage_level: 'medium',
            soil_cover_level: 'medium',
          },
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'Falha ao gerar o plano agroclimatico.');
      }

      setResult(await response.json() as StrategyResponse);
    } catch (planError) {
      setError(planError instanceof Error ? planError.message : 'Falha ao gerar o plano agroclimatico.');
      setResult(null);
    } finally {
      setLoadingPlan(false);
    }
  };

  const topRisks = Object.entries(result?.exposure_scores || {})
    .sort(([, left], [, right]) => right - left)
    .slice(0, 3);

  return (
    <Card className="border-none shadow-soft-xl bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Leaf className="h-6 w-6 text-emerald-500" />
              Estrategia Agroclimatica
            </CardTitle>
            <CardDescription className="mt-2 max-w-2xl text-sm leading-relaxed">
              Gera um plano operacional e financeiro com base em ENSO, forecast NOAA e perfil da lavoura.
            </CardDescription>
          </div>
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600">
            {loadingCatalog ? 'Atualizando catalogo...' : 'ENSO + NOAA'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-8">
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
            <Label htmlFor="agri-stage">Estagio fenologico</Label>
            <Select value={form.phenological_stage} onValueChange={(value) => setForm((current) => ({ ...current, phenological_stage: value }))}>
              <SelectTrigger id="agri-stage">
                <SelectValue placeholder="Selecione o estagio" />
              </SelectTrigger>
              <SelectContent>
                {catalog.supported_stages.map((stage) => (
                  <SelectItem key={stage} value={stage}>{stage}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-risk">Tolerancia ao risco</Label>
            <Select value={form.risk_tolerance} onValueChange={(value: RiskTolerance) => setForm((current) => ({ ...current, risk_tolerance: value }))}>
              <SelectTrigger id="agri-risk">
                <SelectValue placeholder="Selecione a tolerancia" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Baixa</SelectItem>
                <SelectItem value="medium">Media</SelectItem>
                <SelectItem value="high">Alta</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-lat">Latitude</Label>
            <Input id="agri-lat" value={form.latitude} onChange={(event) => setForm((current) => ({ ...current, latitude: event.target.value }))} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-lon">Longitude</Label>
            <Input id="agri-lon" value={form.longitude} onChange={(event) => setForm((current) => ({ ...current, longitude: event.target.value }))} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agri-horizon">Horizonte de planejamento (dias)</Label>
            <Input id="agri-horizon" value={form.planning_horizon_days} onChange={(event) => setForm((current) => ({ ...current, planning_horizon_days: event.target.value }))} />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="button" onClick={handleGeneratePlan} disabled={loadingPlan} className="min-w-52">
            {loadingPlan ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sprout className="mr-2 h-4 w-4" />}
            Gerar plano para o agro
          </Button>
          <div className="text-sm text-muted-foreground">
            Riscos monitorados: {catalog.risk_dimensions.join(', ')}
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
              <div className="grid gap-4 md:grid-cols-3">
                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      Regime ENSO
                    </div>
                    <div className="text-xl font-semibold capitalize text-foreground">
                      {(result.climate_outlook.enso?.regime_label || 'indefinido').replace('_', ' ')}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Confianca {result.climate_outlook.enso?.regime_confidence || 'n/a'}
                    </div>
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
                      Ref. {result.climate_outlook.enso?.reference_date || 'ao vivo'}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border border-border/60 bg-background/50">
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <Leaf className="h-4 w-4" />
                      Maiores exposicoes
                    </div>
                    <div className="space-y-1 text-sm text-foreground">
                      {topRisks.map(([risk, score]) => (
                        <div key={risk} className="flex items-center justify-between gap-3">
                          <span className="capitalize">{risk.replace('_', ' ')}</span>
                          <Badge variant="secondary">{Math.round(score * 100)}%</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="border border-border/60 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-lg">Acoes operacionais</CardTitle>
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
                  <CardTitle className="text-lg">Acoes financeiras</CardTitle>
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