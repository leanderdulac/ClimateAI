/**
 * Weather Widget Component
 * Displays current weather and forecast data from EMBRAPA API
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { lazy, Suspense, useEffect, useState } from 'react';
import { loadEmbrapaApi } from '@/lib/loadEmbrapaApi';
import { useLocation } from '@/lib/LocationContext';
import { usePeriod } from '@/lib/PeriodContext';
import { Sun, Droplets, Wind, Thermometer, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { useTranslation } from '@/hooks/useTranslation';
import type { WeatherChartPoint } from './WeatherWidgetCharts';

const WeatherWidgetCharts = lazy(() =>
  import('./WeatherWidgetCharts').then((module) => ({ default: module.WeatherWidgetCharts }))
);

export function WeatherWidget() {
  const { t } = useTranslation();
  const [climateData, setClimateData] = useState<WeatherChartPoint[]>([]);
  const [currentWeather, setCurrentWeather] = useState<{
    temperature: number;
    humidity: number;
    precipitation: number;
    windSpeed?: number;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [loadingHistorical, setLoadingHistorical] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetailedCharts, setShowDetailedCharts] = useState(false);

  const { selectedLocation, isLoadingLocation } = useLocation();
  const { selectedPeriod } = usePeriod();

  const getWeatherDescription = (temperature: number, humidity: number, precipitation: number) => {
    if (precipitation > 5) return t('weather.conditions.rain');
    if (humidity > 80) return t('weather.conditions.humid');
    if (temperature > 30) return t('weather.conditions.hot');
    if (temperature < 15) return t('weather.conditions.cold');
    return t('weather.conditions.stable');
  };

  useEffect(() => {
    const fetchClimateData = async () => {
      try {
        const embrapaApi = await loadEmbrapaApi();
        console.log('🌤️ [WeatherWidget] Iniciando busca de dados climáticos...');
        setLoading(true);
        setError(null);

        let latitude: number;
        let longitude: number;
        let locationName: string;

        if (selectedLocation) {
          // Usar localização selecionada
          latitude = selectedLocation.latitude;
          longitude = selectedLocation.longitude;
          locationName = `${selectedLocation.cidade || 'Localização'}, ${selectedLocation.estado || ''}`;
          console.log('✅ [WeatherWidget] Usando localização selecionada:', locationName, { latitude, longitude });
        } else {
          // Não buscar dados se nenhuma localização estiver selecionada
          console.log('ℹ️ [WeatherWidget] Nenhuma localização selecionada, aguardando seleção...');
          setLoading(false);
          return;
        }

        // Validar coordenadas
        if (!latitude || !longitude || isNaN(latitude) || isNaN(longitude)) {
          console.error('❌ [WeatherWidget] Coordenadas inválidas:', { latitude, longitude });
          setLoading(false);
          return;
        }

        // Buscar dados históricos baseados no período selecionado
        console.log(`📊 [WeatherWidget] Buscando dados históricos de ${selectedPeriod} dias...`);
        setLoadingHistorical(true);
        try {
          const endDate = new Date();
          const startDate = new Date();
          startDate.setDate(startDate.getDate() - selectedPeriod);

          console.log(`📅 [WeatherWidget] Período: ${startDate.toISOString().split('T')[0]} a ${endDate.toISOString().split('T')[0]}`);

          const historical = await embrapaApi.getClimateData(
            latitude,
            longitude,
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0]
          );

          console.log('📈 [WeatherWidget] Tipo de histórico:', typeof historical, '| Length:', historical?.length);

          // Validar que histórico é um array
          if (!Array.isArray(historical)) {
            console.error('❌ [WeatherWidget] Histórico não é array:', historical);
            setClimateData([]);
            setHistoricalData([]);
            setLoadingHistorical(false);
            return;
          }

          console.log(`📊 [WeatherWidget] Dados históricos recebidos: ${historical.length} pontos`);

          // Usar dados históricos para o gráfico principal
          // Os dados já vêm normalizados do embrapaApi.getClimateData
          const adaptedHistorical: WeatherChartPoint[] = (historical || []).map(item => ({
            date: item.date,
            temperature: item.temperature,
            precipitation: item.precipitation,
          }));

          console.log(`✅ [WeatherWidget] Dados adaptados: ${adaptedHistorical.length} pontos para gráfico`);
          setClimateData(adaptedHistorical);
          setHistoricalData(historical || []);

          // Realizar análise histórica avançada baseada no período selecionado
          console.log(`📊 [WeatherWidget] Realizando análise histórica avançada para ${selectedPeriod} dias...`);
          const historicalAnalysis = await embrapaApi.getHistoricalClimateAnalysis(
            latitude,
            longitude,
            selectedPeriod
          );
          console.log('📈 [WeatherWidget] Análise histórica concluída:', historicalAnalysis);
        } catch (historicalError) {
          console.error('❌ [WeatherWidget] Erro ao buscar dados históricos:', historicalError);
          setHistoricalData([]);
          setClimateData([]);
        } finally {
          setLoadingHistorical(false);
        }

        // Buscar previsão atual (último dia)
        console.log('🌡️ [WeatherWidget] Buscando previsão atual...');
        const currentData = await embrapaApi.getWeatherForecast(latitude, longitude, 1);
        console.log('🌦️ [WeatherWidget] Dados atuais recebidos:', currentData);

        if (currentData.length > 0) {
          // Adaptar formato dos dados do backend para o formato esperado pelo frontend
          const current = currentData[0];
          setCurrentWeather({
            temperature: current.temperature || current.temperatura_max || 20,
            humidity: current.humidity || 60,
            precipitation: current.precipitation || current.precipitacao || 0,
            windSpeed: current.windSpeed || current.vento_velocidade
          });
          console.log('✅ [WeatherWidget] Tempo atual definido:', current.temperature, '°C');
        } else {
          console.warn('⚠️ [WeatherWidget] Sem dados de previsão');
          setCurrentWeather(null);
        }

        setLoading(false);
        console.log('✅ [WeatherWidget] Dados carregados com sucesso');
      } catch (error) {
        console.error('❌ [WeatherWidget] Erro geral ao buscar dados climáticos:', error);
        setLoading(false);
        setLoadingHistorical(false);
        setClimateData([]);
        setError(`${t('weather.error.load')}: ${error instanceof Error ? error.message : String(error)}`);
      }
    };

    // Buscar dados quando o componente monta ou quando a localização/período muda
    console.log(`🔄 [WeatherWidget] Verificando condições: isLoadingLocation=${isLoadingLocation}, selectedLocation=${selectedLocation ? 'sim' : 'não'}`);
    if (!isLoadingLocation) {
      fetchClimateData();
    }
  }, [selectedLocation, isLoadingLocation, selectedPeriod, t]);

  useEffect(() => {
    setShowDetailedCharts(false);

    if (loading || isLoadingLocation || climateData.length === 0) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setShowDetailedCharts(true);
    }, 1200);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [climateData.length, isLoadingLocation, loading, selectedLocation, selectedPeriod]);

  if (error) {
    return (
      <Card className="cc-card overflow-hidden border-destructive/30 bg-destructive/10">
        <CardHeader className="border-none">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-destructive/20 p-3">
              <AlertTriangle className="h-6 w-6 text-red-400" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-red-300">{t('weather.error.title')}</CardTitle>
              <CardDescription className="text-red-300/80">
                {error}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  if (loading || isLoadingLocation) {
    return (
      <Card className="cc-card h-full overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl">
        <CardHeader className="cc-header border-none">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-amber-500/10 p-3 text-amber-400">
              <Sun className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-foreground">{t('weather.title')}</CardTitle>
              <CardDescription>
                {isLoadingLocation ? t('weather.loadingLocation') : t('weather.loading')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="cc-card h-full overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl">
      <CardHeader className="cc-header border-border/40">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-amber-500/10 p-3 text-amber-400">
            <Sun className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-xl font-bold text-foreground">
                {selectedLocation ? `${selectedLocation.cidade}, ${selectedLocation.estado}` : t('weather.title')}
              </CardTitle>
              {currentWeather && (
                <Badge variant="outline" className="h-5 gap-1 border-amber-500/30 bg-amber-500/10 px-1.5 py-0 text-[10px] font-bold uppercase tracking-wider text-amber-400">
                  <Zap className="h-2.5 w-2.5 fill-amber-400 text-amber-400" />
                  {t('weather.liveBadge')}
                </Badge>
              )}
            </div>
            <CardDescription>
              {currentWeather ? `${getWeatherDescription(
                currentWeather.temperature,
                currentWeather.humidity,
                currentWeather.precipitation
              )} • ${historicalData.length > 0 ? `${historicalData.length} ${t('weather.historicalData')}` : t('weather.noHistorical')}` : t('common.loading')}
              {loadingHistorical && ` • ${t('weather.loadingHistorical')}`}
            </CardDescription>
          </div>
        </div>
        {currentWeather && (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:flex sm:items-center">
            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/30 px-4 py-2">
              <Thermometer className="h-5 w-5 text-amber-400" />
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{t('weather.temperature')}</div>
                <div className="text-lg font-semibold text-foreground">
                  {currentWeather.temperature.toFixed(1)}°C
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/30 px-4 py-2">
              <Droplets className="h-5 w-5 text-blue-400" />
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{t('weather.rain')}</div>
                <div className="text-lg font-semibold text-foreground">
                  {currentWeather.precipitation.toFixed(1)}mm
                </div>
              </div>
            </div>
            {currentWeather.windSpeed && (
              <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/30 px-4 py-2">
                <Wind className="h-5 w-5 text-emerald-400" />
                <div>
                  <div className="text-xs uppercase tracking-wider text-muted-foreground">{t('weather.wind')}</div>
                  <div className="text-lg font-semibold text-foreground">
                    {currentWeather.windSpeed.toFixed(1)}km/h
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-8 p-6">
        {showDetailedCharts ? (
          <Suspense
            fallback={
              <div className="space-y-8">
                <div className="h-[286px] rounded-xl bg-muted animate-pulse" />
                <div className="h-[286px] rounded-xl bg-muted animate-pulse" />
              </div>
            }
          >
            <WeatherWidgetCharts climateData={climateData} />
          </Suspense>
        ) : (
          <div className="rounded-xl border border-dashed border-border/70 bg-muted/30 px-4 py-6 text-sm text-muted-foreground">
            {t('weather.loadingHistorical')}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
