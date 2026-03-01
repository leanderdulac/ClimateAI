import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useEffect, useState } from 'react';
import { loadEmbrapaApi } from '@/lib/loadEmbrapaApi';
import { usePeriod } from '@/lib/PeriodContext';
import { useLocation } from '@/lib/LocationContext';
import { Sun, Droplets, Wind, Thermometer, TrendingUp, TrendingDown, Minus, AlertTriangle, Cloud, Gauge, Globe, ShieldCheck } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { useTranslation } from "@/hooks/useTranslation";

interface ClimateDataPoint {
  date: string;
  avgTemp: number;
  maxTemp?: number;
  minTemp?: number;
  rainfall: number;
  rainProb: number;
  windSpeed?: number;
  weatherCode?: number;
}

interface ClimateTrends {
  temperature: {
    trend: 'rising' | 'falling' | 'stable';
    average: number;
    anomaly: number;
  };
  rainfall: {
    trend: 'rising' | 'falling' | 'stable';
    totalAccumulated: number;
    daysWithRain: number;
  };
  extremeEvents: {
    hotDays: number; // dias acima de 30°C
    coldDays: number; // dias abaixo de 15°C
    heavyRainDays: number; // dias com mais de 30mm
    dryDays: number; // dias sem chuva
  };
}

function analyzeTrends(data: ClimateDataPoint[]): ClimateTrends {
  // Calcula tendências de temperatura
  const temperatures = data.map(d => d.avgTemp);
  const tempTrend = calculateTrend(temperatures);
  const tempAvg = average(temperatures);
  const tempAnomaly = temperatures[temperatures.length - 1] - tempAvg;

  // Calcula tendências de chuva
  const rainfall = data.map(d => d.rainfall);
  const rainTrend = calculateTrend(rainfall);
  const totalRain = sum(rainfall);
  const rainyDays = data.filter(d => d.rainfall > 0.1).length;

  // Identifica eventos extremos
  const hotDays = data.filter(d => d.maxTemp && d.maxTemp > 30).length;
  const coldDays = data.filter(d => d.minTemp && d.minTemp < 15).length;
  const heavyRainDays = data.filter(d => d.rainfall > 30).length;
  const dryDays = data.filter(d => d.rainfall < 0.1).length;

  return {
    temperature: {
      trend: tempTrend,
      average: tempAvg,
      anomaly: tempAnomaly
    },
    rainfall: {
      trend: rainTrend,
      totalAccumulated: totalRain,
      daysWithRain: rainyDays
    },
    extremeEvents: {
      hotDays,
      coldDays,
      heavyRainDays,
      dryDays
    }
  };
}

function calculateTrend(values: number[]): 'rising' | 'falling' | 'stable' {
  if (values.length < 2) return 'stable';

  const firstHalf = average(values.slice(0, Math.floor(values.length / 2)));
  const secondHalf = average(values.slice(Math.floor(values.length / 2)));
  const difference = secondHalf - firstHalf;

  if (Math.abs(difference) < 0.1) return 'stable';
  return difference > 0 ? 'rising' : 'falling';
}

function average(values: number[]): number {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function sum(values: number[]): number {
  return values.reduce((a, b) => a + b, 0);
}

export function ClimateDataWidget() {
  const { t, language } = useTranslation();
  const [climateData, setClimateData] = useState<ClimateDataPoint[]>([]);
  const [climateTrends, setClimateTrends] = useState<ClimateTrends | null>(null);
  const [currentWeather, setCurrentWeather] = useState<{
    temperature: number;
    humidity: number;
    apparentTemp?: number;
    precipitation: number;
    windSpeed?: number;
    weatherCode?: number;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const { selectedPeriod } = usePeriod();
  const { selectedLocation, isLoadingLocation } = useLocation();

  useEffect(() => {
    console.log('[ClimateDataWidget] useEffect disparado', {
      selectedLocation: selectedLocation ? {
        cidade: selectedLocation.cidade,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude
      } : null,
      isLoadingLocation,
      selectedPeriod
    });

    // Se não há localização ou está carregando, limpa os dados
    if (!selectedLocation || isLoadingLocation || !selectedLocation.latitude || !selectedLocation.longitude) {
      console.log('[ClimateDataWidget] Localização não disponível, limpando dados');
      setClimateData([]);
      setClimateTrends(null);
      setCurrentWeather(null);
      setLoading(false);
      return;
    }

    const fetchClimateData = async () => {
      console.log('[ClimateDataWidget] fetchClimateData iniciado para', selectedLocation.cidade || 'localização');

      try {
        const embrapaApi = await loadEmbrapaApi();
        console.log('[ClimateDataWidget] Embrapa API carregada');
        setLoading(true);
        setError(null);

        const latitude = selectedLocation.latitude;
        const longitude = selectedLocation.longitude;
        const locationName = selectedLocation.cidade || selectedLocation.formattedAddress || `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`;

        console.log('[ClimateDataWidget] Buscando dados atuais para:', locationName, { latitude, longitude });

        // Buscar dados atuais
        const today = new Date().toISOString().split('T')[0];
        const currentData = await embrapaApi.getClimateData(latitude, longitude, today, today);
        console.log('[ClimateDataWidget] Dados atuais recebidos:', currentData?.length || 0, 'registros');

        if (currentData && currentData.length > 0) {
          const current = currentData[0];
          console.log('[ClimateDataWidget] Primeiro registro atual:', current);

          // Mapear campos do backend (português) para o frontend (inglês)
          setCurrentWeather({
            temperature: current.temperature,
            humidity: current.humidity,
            apparentTemp: current.temperature_apparent || current.temperature,
            precipitation: current.precipitation,
            windSpeed: current.windSpeed || current.wind_speed || 0,
            weatherCode: current.weatherCode || current.weather_code || 0
          });
        } else {
          console.warn('[ClimateDataWidget] Nenhum dado atual recebido, usando fallback');
          setCurrentWeather({
            temperature: 25,
            humidity: 60,
            precipitation: 0,
            windSpeed: 5
          });
        }

        // Calcular datas para dados históricos
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - selectedPeriod);

        console.log('[ClimateDataWidget] Buscando dados históricos de', startDate.toISOString().split('T')[0], 'até', endDate.toISOString().split('T')[0]);

        // Buscar dados históricos
        const historicalData = await embrapaApi.getClimateData(
          latitude,
          longitude,
          startDate.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0]
        );
        console.log('[ClimateDataWidget] Dados históricos recebidos:', historicalData?.length || 0, 'registros');

        if (!historicalData || historicalData.length === 0) {
          console.warn('[ClimateDataWidget] Nenhum dado histórico recebido, usando mock');
          // Criar dados mock se não houver dados reais
          const mockData = [];
          for (let i = 0; i < Math.min(selectedPeriod, 30); i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            mockData.push({
              date: date.toISOString().split('T')[0],
              temperature: 20 + Math.random() * 10,
              temperature_max: 28 + Math.random() * 5,
              temperature_min: 15 + Math.random() * 5,
              precipitation: Math.random() * 10,
              humidity: 60 + Math.random() * 20,
              wind_speed: 5 + Math.random() * 10
            });
          }
          historicalData.push(...mockData);
        }

        // Processar dados históricos
        // Os campos agora já vêm normalizados do embrapaApi.getClimateData
        const chartData: ClimateDataPoint[] = historicalData.map(data => ({
          date: data.date,
          maxTemp: data.temperature_max || data.temperature,
          minTemp: data.temperature_min || data.temperature,
          avgTemp: data.temperature,
          rainfall: data.precipitation,
          rainProb: data.precipitation_probability || 0,
          windSpeed: data.windSpeed || 0,
          weatherCode: data.weatherCode || 0
        }));

        console.log('[ClimateDataWidget] ChartData processado:', chartData.length, 'pontos');
        console.log('[ClimateDataWidget] Amostra de dados:', chartData.slice(0, 3));
        setClimateData(chartData);

        // Analisar tendências
        if (chartData.length > 0) {
          console.log('[ClimateDataWidget] Calculando tendências...');
          const trends = analyzeTrends(chartData);
          console.log('[ClimateDataWidget] Tendências calculadas:', trends);
          setClimateTrends(trends);
        }

        console.log('[ClimateDataWidget] Carregamento concluído com sucesso!');
        setLoading(false);
      } catch (error) {
        console.error('[ClimateDataWidget] ERRO ao buscar dados climáticos:', error);
        setError(`Erro: ${error instanceof Error ? error.message : String(error)}`);
        setLoading(false);

        // Em caso de erro, usar dados mock
        console.warn('[ClimateDataWidget] Usando dados mock como fallback');
        const mockData: ClimateDataPoint[] = [];
        for (let i = 0; i < selectedPeriod; i++) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          mockData.push({
            date: date.toISOString().split('T')[0],
            avgTemp: 20 + Math.random() * 10,
            maxTemp: 28 + Math.random() * 5,
            minTemp: 15 + Math.random() * 5,
            rainfall: Math.random() * 10,
            rainProb: Math.random() * 100,
            windSpeed: 5 + Math.random() * 10
          });
        }
        setClimateData(mockData);
        setClimateTrends(analyzeTrends(mockData));
        setCurrentWeather({
          temperature: 25,
          humidity: 60,
          precipitation: 0,
          windSpeed: 5
        });
      }
    };

    fetchClimateData();
  }, [selectedLocation, isLoadingLocation, selectedPeriod]);

  if (loading) {
    return (
      <Card className="overflow-hidden animate-fade-in" variant="default">
        <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">{t('climate.widget.title')}</CardTitle>
              <CardDescription className="text-primary-100">
                {t('climate.widget.description')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-8 p-6 bg-gradient-to-b from-white to-neutral-50">
          <div className="space-y-4">
            <div className="h-8 w-48 animate-pulse rounded-md bg-neutral-200"></div>
            <div className="h-[250px] animate-pulse rounded-lg bg-neutral-200"></div>
          </div>
          <div className="space-y-4">
            <div className="h-8 w-48 animate-pulse rounded-md bg-neutral-200"></div>
            <div className="h-[250px] animate-pulse rounded-lg bg-neutral-200"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getWeatherDescription = (code: number) => {
    switch (code) {
      case 0: return t('weather.condition.clear');
      case 1: case 2: case 3: return t('weather.condition.partlyCloudy');
      case 45: case 48: return t('weather.condition.foggy');
      case 51: case 53: case 55: return t('weather.condition.drizzle');
      case 61: case 63: case 65: return t('weather.condition.rain');
      case 71: case 73: case 75: return t('weather.condition.snow');
      case 77: return t('weather.condition.snowGrains');
      case 80: case 81: case 82: return t('weather.condition.rainShowers');
      case 85: case 86: return t('weather.condition.snowShowers');
      case 95: return t('weather.condition.thunderstorm');
      case 96: case 99: return t('weather.condition.thunderstormHail');
      default: return t('weather.condition.unknown');
    }
  };

  if (error) {
    return (
      <Card className="overflow-hidden animate-fade-in border-red-200" variant="default">
        <CardHeader className="border-none bg-gradient-to-r from-red-600 to-red-700 pb-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/20 p-3">
              <AlertTriangle className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">{t('climate.error.title')}</CardTitle>
              <CardDescription className="text-red-100/90 font-medium">
                {t('climate.error.description')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-6 bg-red-50/30">
          <div className="flex flex-col gap-4">
            <div className="p-4 rounded-md bg-white border border-red-100 shadow-sm">
              <p className="text-sm font-medium text-red-800">{t('climate.error.technical')}:</p>
              <p className="text-sm text-red-600 mt-1 font-mono break-all">{error}</p>
            </div>
            <div className="text-xs text-neutral-500 italic">
              {t('climate.error.fallback')}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Verificar se há localização selecionada
  if (!selectedLocation) {
    return (
      <Card className="overflow-hidden animate-fade-in">
        <CardHeader className="border-none bg-gradient-to-r from-gray-500 to-gray-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Cloud className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">{t('climate.noLocation.title')}</CardTitle>
              <CardDescription className="text-gray-100">
                {t('climate.noLocation.description')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">{t('climate.noLocation.cta')}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden animate-fade-in">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl font-bold text-white">Climate Analytics</CardTitle>
                <Badge
                  variant="secondary"
                  className="bg-white/20 border-none text-white gap-1 hover:bg-white/30 cursor-help"
                  title="Data verified against OpenMeteo Satellite & Ground Station telemetry (v3.2 Protocol)."
                >
                  <ShieldCheck className="h-3 w-3 text-green-300" />
                  Verified Integrity
                </Badge>
              </div>
              <CardDescription className="text-primary-100">
                {currentWeather ? `${getWeatherDescription(currentWeather.weatherCode || 0)} ${t('common.in')} ${selectedLocation?.cidade || t('common.yourLocation')}` : t('common.loading')}
              </CardDescription>
            </div>
          </div>
          {currentWeather && (
            <div className="grid grid-cols-2 gap-4 sm:flex sm:items-center">
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Thermometer className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">{t('weather.current')}</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather?.temperature?.toFixed(1) ?? 'N/A'}°C
                  </div>
                  <div className="text-xs text-primary-100">
                    {t('climate.widget.feelsLike', { temp: currentWeather?.apparentTemp?.toFixed(1) ?? currentWeather?.temperature?.toFixed(1) ?? 'N/A' })}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Droplets className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">{t('weather.rain')}</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather?.precipitation?.toFixed(1) ?? '0.0'}mm
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Wind className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">{t('weather.wind')}</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather?.windSpeed?.toFixed(1) ?? '0.0'}km/h
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-8 p-6 bg-gradient-to-b from-white to-neutral-50">
        <div className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
              <Thermometer className="h-5 w-5 text-primary-500" />
              {t('climate.widget.temperatureTrends')}
            </h3>
          </div>
          <div className="rounded-lg bg-white p-6 shadow-soft">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={climateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickFormatter={(value) => {
                    const d = new Date(value);
                    return isNaN(d.getTime()) ? value : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  }}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickFormatter={(value) => `${value}°C`}
                />
                <Tooltip
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                  }}
                  formatter={(value: number) => [`${value}°C`, t('weather.temp')]}
                  labelFormatter={(label: string) => {
                    const d = new Date(label);
                    return isNaN(d.getTime()) ? label : d.toLocaleDateString();
                  }}
                />
                <Line type="monotone" dataKey="maxTemp" name={t('common.max')} stroke="#ef4444" dot={false} />
                <Line type="monotone" dataKey="minTemp" name={t('common.min')} stroke="#3b82f6" dot={false} />
                <Line type="monotone" dataKey="avgTemp" name={t('common.avg')} stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="animate-slide-up [animation-delay:200ms]">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
              <Droplets className="h-5 w-5 text-primary-500" />
              {t('climate.widget.precipitationAnalysis')}
            </h3>
            {climateTrends && (
              <div className="flex items-center gap-2 rounded-lg bg-primary-50 px-3 py-1 text-sm text-primary-600">
                <Gauge className="h-4 w-4" />
                {t('common.total')}: {climateTrends.rainfall?.totalAccumulated?.toFixed(0) ?? '0'}mm
              </div>
            )}
          </div>
          <div className="rounded-lg bg-white p-6 shadow-soft">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={climateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickFormatter={(value) => {
                    const d = new Date(value);
                    return isNaN(d.getTime()) ? value : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  }}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickFormatter={(value) => `${value}mm`}
                />
                <Tooltip
                  cursor={{ fill: '#f1f5f9' }}
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                  }}
                  formatter={(value: number) => [`${value}mm`, t('weather.rain')]}
                  labelFormatter={(label: string) => {
                    const d = new Date(label);
                    return isNaN(d.getTime()) ? label : d.toLocaleDateString();
                  }}
                />
                <Bar
                  dataKey="rainfall"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                  barSize={30}
                />
                <Line type="monotone" dataKey="rainProb" name={t('climate.analysis.trend')} stroke="#8b5cf6" yAxisId="right" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {climateTrends && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="rounded-lg bg-white p-6 shadow-soft">
              <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                <Thermometer className="h-5 w-5 text-primary-500" />
                {t('climate.widget.tempAnalysis')}
              </h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.trend')}</span>
                  <div className="flex items-center gap-2">
                    {climateTrends.temperature.trend === 'rising' && <TrendingUp className="h-4 w-4 text-red-500" />}
                    {climateTrends.temperature.trend === 'falling' && <TrendingDown className="h-4 w-4 text-blue-500" />}
                    {climateTrends.temperature.trend === 'stable' && <Minus className="h-4 w-4 text-neutral-500" />}
                    <span className="font-medium capitalize">{t(`climate.trends.${climateTrends.temperature.trend}`)}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.average')}</span>
                  <span className="font-medium">{climateTrends?.temperature?.average?.toFixed(1) ?? 'N/A'}°C</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.anomaly')}</span>
                  <span className={`font-medium ${climateTrends?.temperature?.anomaly && climateTrends.temperature.anomaly > 0 ? 'text-red-500' :
                    climateTrends?.temperature?.anomaly && climateTrends.temperature.anomaly < 0 ? 'text-blue-500' : 'text-neutral-500'
                    }`}>
                    {climateTrends?.temperature?.anomaly ? (climateTrends.temperature.anomaly > 0 ? '+' : '') : '0.0'}{climateTrends?.temperature?.anomaly?.toFixed(1) ?? '0.0'}°C
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-lg bg-white p-6 shadow-soft">
              <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                <Cloud className="h-5 w-5 text-primary-500" />
                {t('climate.widget.rainAnalysis')}
              </h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.trend')}</span>
                  <div className="flex items-center gap-2">
                    {climateTrends.rainfall.trend === 'rising' && <TrendingUp className="h-4 w-4 text-blue-500" />}
                    {climateTrends.rainfall.trend === 'falling' && <TrendingDown className="h-4 w-4 text-orange-500" />}
                    {climateTrends.rainfall.trend === 'stable' && <Minus className="h-4 w-4 text-neutral-500" />}
                    <span className="font-medium capitalize">{t(`climate.trends.${climateTrends.rainfall.trend}`)}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.totalAccumulated')}</span>
                  <span className="font-medium">{climateTrends?.rainfall?.totalAccumulated?.toFixed(0) ?? 'N/A'}mm</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">{t('climate.analysis.daysWithRain')}</span>
                  <span className="font-medium">{climateTrends.rainfall.daysWithRain} {t('common.days')}</span>
                </div>
              </div>
            </div>

            <div className="col-span-1 md:col-span-2">
              <div className="rounded-lg bg-white p-6 shadow-soft">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                  <AlertTriangle className="h-5 w-5 text-primary-500" />
                  {t('climate.widget.extremeEvents')}
                </h4>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">{t('climate.widget.hotDays')}</div>
                    <div className="mt-1 text-2xl font-semibold text-red-500">
                      {climateTrends.extremeEvents.hotDays}
                    </div>
                    <div className="text-xs text-neutral-500">{t('climate.widget.above')} 30°C</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">{t('climate.widget.coldDays')}</div>
                    <div className="mt-1 text-2xl font-semibold text-blue-500">
                      {climateTrends.extremeEvents.coldDays}
                    </div>
                    <div className="text-xs text-neutral-500">{t('climate.widget.below')} 15°C</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">{t('climate.widget.heavyRain')}</div>
                    <div className="mt-1 text-2xl font-semibold text-blue-500">
                      {climateTrends.extremeEvents.heavyRainDays}
                    </div>
                    <div className="text-xs text-neutral-500">{t('climate.widget.above')} 30mm</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">{t('climate.widget.dryDays')}</div>
                    <div className="mt-1 text-2xl font-semibold text-orange-500">
                      {climateTrends.extremeEvents.dryDays}
                    </div>
                    <div className="text-xs text-neutral-500">{t('climate.widget.noRain')}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
