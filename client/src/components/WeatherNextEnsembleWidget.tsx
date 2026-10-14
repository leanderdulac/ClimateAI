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

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLocation } from '@/lib/LocationContext';
import { weathernextApi, type EnsembleForecast } from '@/lib/api/weathernext';
import { isFeatureEnabled } from '@/lib/features';
import { useTranslation } from '@/hooks/useTranslation';
import { commandCenterChart } from '@/lib/commandCenterChart';

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
    return (data?.hourly_fan ?? []).map((point) => {
      const p10 = point.temperature_p10_c ?? 0;
      const p90 = point.temperature_p90_c ?? p10;
      return {
        time: new Date(point.time_local).toLocaleString(t('locale') || 'pt-BR', {
          day: '2-digit',
          hour: '2-digit',
        }),
        p10,
        p50: point.temperature_p50_c,
        p90,
        spread: Math.max(p90 - p10, 0),
      };
    });
  }, [data, t]);

  if (!isFeatureEnabled('weathernext')) {
    return null;
  }

  if (!selectedLocation) {
    return (
      <Card className="cc-card overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl">
        <CardHeader className="cc-header border-border/40">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-cyan-500/10 p-3 text-cyan-400">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-foreground">{t('weathernext.title')}</CardTitle>
              <CardDescription>{t('weathernext.subtitle')}</CardDescription>
            </div>
          </div>
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
    <Card className="cc-card w-full overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl">
      <CardHeader className="cc-header border-border/40">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-cyan-500/10 p-3 text-cyan-400">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-xl font-bold text-foreground">{t('weathernext.title')}</CardTitle>
                <Badge variant="outline" className="h-5 border-cyan-500/30 bg-cyan-500/10 px-1.5 py-0 text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                  WeatherNext 2
                </Badge>
              </div>
              <CardDescription>{t('weathernext.subtitle')}</CardDescription>
            </div>
          </div>
        </div>
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
                    <CartesianGrid strokeDasharray="3 3" stroke={commandCenterChart.grid} />
                    <XAxis dataKey="time" stroke={commandCenterChart.axis} tick={{ fill: commandCenterChart.tick, fontSize: 11 }} />
                    <YAxis unit="°C" stroke={commandCenterChart.axis} tick={{ fill: commandCenterChart.tick, fontSize: 11 }} />
                    <Tooltip contentStyle={commandCenterChart.tooltip} />
                    <Area
                      type="monotone"
                      dataKey="p10"
                      stackId="fan"
                      stroke="none"
                      fill="transparent"
                      name="p10"
                    />
                    <Area
                      type="monotone"
                      dataKey="spread"
                      stackId="fan"
                      stroke="none"
                      fill="rgba(96,165,250,0.28)"
                      name="p10–p90"
                    />
                    <Line type="monotone" dataKey="p50" stroke={commandCenterChart.blue} dot={false} strokeWidth={2} name="p50" />
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
