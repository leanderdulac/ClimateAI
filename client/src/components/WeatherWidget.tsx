/**
 * Weather Widget Component
 * Displays current weather and forecast data from EMBRAPA API
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useEffect, useState } from 'react';
import { loadEmbrapaApi } from '@/lib/loadEmbrapaApi';
import { useLocation } from '@/lib/LocationContext';
import { usePeriod } from '@/lib/PeriodContext';
import { Sun, Droplets, Wind, Thermometer, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { useTranslation } from '@/hooks/useTranslation';

interface ClimateDataPoint {
  date: string;
  temperature: number;
  precipitation: number;
  humidity: number;
  windSpeed?: number;
  cloudCover?: number;
}

export function WeatherWidget() {
  const { t } = useTranslation();
  const [climateData, setClimateData] = useState<ClimateDataPoint[]>([]);
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
          const adaptedHistorical: ClimateDataPoint[] = (historical || []).map(item => ({
            date: item.date,
            temperature: item.temperature,
            precipitation: item.precipitation,
            humidity: item.humidity,
            windSpeed: item.windSpeed
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

  if (error) {
    return (
      <Card className="overflow-hidden bg-red-50">
        <CardHeader className="border-none">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-red-100 p-3">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-red-700">{t('weather.error.title')}</CardTitle>
              <CardDescription className="text-red-600">
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
      <Card className="overflow-hidden">
        <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">{t('weather.title')}</CardTitle>
              <CardDescription className="text-primary-100">
                {isLoadingLocation ? t('weather.loadingLocation') : t('weather.loading')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex items-center gap-4">
          <div className="rounded-lg bg-white/10 p-3">
            <Sun className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-xl font-bold text-white">
                {selectedLocation ? `${selectedLocation.cidade}, ${selectedLocation.estado}` : t('weather.title')}
              </CardTitle>
              {currentWeather && (
                <Badge variant="outline" className="bg-white/20 border-white/40 text-white gap-1 px-1.5 py-0 h-5 text-[10px] uppercase font-bold tracking-wider">
                  <Zap className="h-2.5 w-2.5 fill-yellow-400 text-yellow-400" />
                  {t('weather.liveBadge')}
                </Badge>
              )}
            </div>
            <CardDescription className="text-primary-100">
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
          <div className="grid grid-cols-2 gap-4 sm:flex sm:items-center mt-4">
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Thermometer className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">{t('weather.temperature')}</div>
                <div className="text-lg font-semibold text-white">
                  {currentWeather.temperature.toFixed(1)}°C
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Droplets className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">{t('weather.rain')}</div>
                <div className="text-lg font-semibold text-white">
                  {currentWeather.precipitation.toFixed(1)}mm
                </div>
              </div>
            </div>
            {currentWeather.windSpeed && (
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Wind className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">{t('weather.wind')}</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather.windSpeed.toFixed(1)}km/h
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-8 p-6">
        <div>
          <h3 className="mb-4 text-lg font-semibold">{t('weather.temperatureOverTime')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={climateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString(t('locale') || 'pt-BR')}
              />
              <YAxis unit="°C" />
              <Tooltip
                labelFormatter={(label) => {
                  const d = new Date(label);
                  return isNaN(d.getTime()) ? label : d.toLocaleDateString(t('locale') || 'pt-BR');
                }}
                formatter={(value: any) => [Number(value).toFixed(1) + "°C", t('weather.temperature')]}
              />
              <Line
                type="monotone"
                dataKey="temperature"
                name={t('weather.temperature')}
                stroke="#10b981"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h3 className="mb-4 text-lg font-semibold">{t('weather.precipitation')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={climateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString(t('locale') || 'pt-BR')}
              />
              <YAxis unit="mm" />
              <Tooltip
                labelFormatter={(label) => {
                  const d = new Date(label);
                  return isNaN(d.getTime()) ? label : d.toLocaleDateString(t('locale') || 'pt-BR');
                }}
                formatter={(value: any) => [Number(value).toFixed(1) + "mm", t('weather.rain')]}
              />
              <Bar
                dataKey="precipitation"
                name={t('weather.rain')}
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
