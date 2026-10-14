import { useEffect, useMemo, useState } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Activity, CloudRain, Loader2, Thermometer } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLocation } from '@/lib/LocationContext';
import { weathernextApi, type EnsembleForecast } from '@/lib/api/weathernext';
import { isFeatureEnabled } from '@/lib/features';
import { useTranslation } from '@/hooks/useTranslation';

function formatPct(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Math.round(value * 100)}%`;
}

export function WeatherNextEnsembleWidget() {
  const { t } = useTranslation();
  const { selectedLocation } = useLocation();
  const [data, setData] = useState<EnsembleForecast | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isFeatureEnabled('weathernext') || !selectedLocation) {
      setData(null);
      return;
    }

    let cancelled = false;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const forecast = await weathernextApi.getPoint(
          selectedLocation.latitude,
          selectedLocation.longitude
        );
        if (!cancelled) setData(forecast);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t('weathernext.error'));
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [selectedLocation, t]);

  const chartData = useMemo(() => {
    return (data?.hourly_fan ?? []).map((point) => ({
      time: new Date(point.time_local).toLocaleString(t('locale') || 'pt-BR', {
        day: '2-digit',
        hour: '2-digit',
      }),
      p10: point.temperature_p10_c,
      p50: point.temperature_p50_c,
      p90: point.temperature_p90_c,
      band: (point.temperature_p90_c ?? 0) - (point.temperature_p10_c ?? 0),
    }));
  }, [data, t]);

  if (!isFeatureEnabled('weathernext')) {
    return null;
  }

  if (!selectedLocation) {
    return (
      <Card className="glass-card border-0 shadow-2xl overflow-hidden">
        <CardHeader className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-700 opacity-90" />
          <CardTitle className="relative z-10 text-white text-xl font-bold">
            {t('weathernext.title')}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 text-sm text-muted-foreground">
          {t('weathernext.selectLocation')}
        </CardContent>
      </Card>
    );
  }

  const exceedance = data?.pricing_exceedance;
  const precipEntries = Object.entries(exceedance?.precip_exceedance ?? {});
  const heatEntries = Object.entries(exceedance?.heat_exceedance ?? {});

  return (
    <Card className="w-full overflow-hidden glass-card border-0 shadow-2xl group">
      <CardHeader className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-700 opacity-90" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20" />
        <CardTitle className="relative z-10 flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <div className="text-sm font-normal text-white/80">{t('weathernext.subtitle')}</div>
              <div className="text-xl font-bold">{t('weathernext.title')}</div>
            </div>
          </div>
          <Badge className="bg-white/20 text-white border-white/30 hover:bg-white/30">
            WeatherNext 2
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t('weathernext.loading')}
          </div>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {!loading && data && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-2xl border border-border/60 bg-card/50 p-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                  <CloudRain className="h-4 w-4 text-cyan-500" />
                  {t('weathernext.heavyRain')}
                </div>
                <div className="text-2xl font-bold">{formatPct(exceedance?.p_heavy_rain)}</div>
              </div>
              <div className="rounded-2xl border border-border/60 bg-card/50 p-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                  <Thermometer className="h-4 w-4 text-orange-500" />
                  {t('weathernext.members')}
                </div>
                <div className="text-2xl font-bold">{data.daily[0]?.member_count ?? '—'}</div>
              </div>
              <div className="rounded-2xl border border-border/60 bg-card/50 p-4">
                <div className="text-xs text-muted-foreground mb-1">{t('weathernext.horizon')}</div>
                <div className="text-2xl font-bold">{exceedance?.horizon_days ?? data.daily.length}d</div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold mb-3">{t('weathernext.fanChart')}</h3>
              <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                    <YAxis unit="°C" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="p90"
                      stroke="none"
                      fill="rgba(34,211,238,0.18)"
                      name="p90"
                    />
                    <Area
                      type="monotone"
                      dataKey="p10"
                      stroke="none"
                      fill="rgba(15,23,42,0.35)"
                      name="p10"
                    />
                    <Line type="monotone" dataKey="p50" stroke="#22d3ee" dot={false} strokeWidth={2} name="p50" />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold mb-3">{t('weathernext.precipExceedance')}</h3>
                <div className="space-y-3">
                  {precipEntries.map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span>{key.replace('ge_', '≥ ').replace('mm', ' mm')}</span>
                        <span className="font-semibold">{formatPct(value)}</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-blue-600"
                          style={{ width: `${Math.round(value * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-3">{t('weathernext.heatExceedance')}</h3>
                <div className="space-y-3">
                  {heatEntries.map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span>{key.replace('ge_', '≥ ').replace('c', ' °C')}</span>
                        <span className="font-semibold">{formatPct(value)}</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-orange-400 to-red-500"
                          style={{ width: `${Math.round(value * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
