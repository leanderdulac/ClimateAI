import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useEffect, useState } from 'react';
import { embrapaApi } from '@/lib/embrapaApi';
import { usePeriod } from '@/lib/PeriodContext';
import { Sun, Droplets, Wind, Thermometer, TrendingUp, TrendingDown, Minus, AlertTriangle, Cloud, Gauge } from 'lucide-react';

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

interface ClimateDataWidgetProps {
  latitude?: number;
  longitude?: number;
}

export function ClimateDataWidget({ latitude = -23.5505, longitude = -46.6333 }: ClimateDataWidgetProps) {
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

  useEffect(() => {
    const fetchClimateData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Obter dados atuais primeiro
        const currentData = await embrapaApi.getClimateData(
          latitude,
          longitude,
          new Date().toISOString().split('T')[0],
          new Date().toISOString().split('T')[0]
        );

        if (currentData && currentData.length > 0) {
          setCurrentWeather({
            temperature: currentData[0].temperature,
            humidity: currentData[0].humidity,
            apparentTemp: currentData[0].temperature_apparent,
            precipitation: currentData[0].precipitation,
            windSpeed: currentData[0].wind_speed || currentData[0].windSpeed,
            weatherCode: currentData[0].weather_code || 0
          });
        }

        // Calcular datas para dados históricos baseados no período selecionado
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - selectedPeriod);

        // Buscar dados históricos
        const historicalData = await embrapaApi.getClimateData(
          latitude,
          longitude,
          startDate.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0]
        );

        // Processar dados históricos
        const chartData: ClimateDataPoint[] = historicalData.map(data => ({
          date: data.date,
          maxTemp: data.temperature_max || data.temperature,
          minTemp: data.temperature_min || data.temperature,
          avgTemp: data.temperature,
          rainfall: data.precipitation,
          rainProb: data.precipitation_probability || 0,
          windSpeed: data.wind_speed || data.windSpeed,
          weatherCode: data.weather_code || 0
        }));

        setClimateData(chartData);

        // Analisar tendências
        if (chartData.length > 0) {
          const trends = analyzeTrends(chartData);
          setClimateTrends(trends);
        }

        setLoading(false);
      } catch (error) {
        console.error('Erro ao buscar dados climáticos:', error);
        setError('Não foi possível carregar os dados climáticos');
        setLoading(false);
      }
    };

    if (latitude && longitude) {
      fetchClimateData();
    }
  }, [latitude, longitude]);

  if (loading) {
    return (
      <Card className="overflow-hidden animate-fade-in" variant="default">
        <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Climate Analytics</CardTitle>
              <CardDescription className="text-primary-100">
                Loading climate patterns for your region...
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
      case 0: return 'Clear sky';
      case 1: case 2: case 3: return 'Partly cloudy';
      case 45: case 48: return 'Foggy';
      case 51: case 53: case 55: return 'Drizzle';
      case 61: case 63: case 65: return 'Rain';
      case 71: case 73: case 75: return 'Snow';
      case 77: return 'Snow grains';
      case 80: case 81: case 82: return 'Rain showers';
      case 85: case 86: return 'Snow showers';
      case 95: return 'Thunderstorm';
      case 96: case 99: return 'Thunderstorm with hail';
      default: return 'Unknown';
    }
  };

  if (error) {
    return (
      <Card className="overflow-hidden animate-fade-in" variant="default">
        <CardHeader className="border-none bg-gradient-to-r from-red-500 to-red-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <AlertTriangle className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Error</CardTitle>
              <CardDescription className="text-primary-100">
                {error}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
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
              <CardTitle className="text-xl font-bold text-white">Climate Analytics</CardTitle>
              <CardDescription className="text-primary-100">
                {currentWeather ? `${getWeatherDescription(currentWeather.weatherCode || 0)} in São Paulo` : 'Loading weather data...'}
              </CardDescription>
            </div>
          </div>
          {currentWeather && (
            <div className="grid grid-cols-2 gap-4 sm:flex sm:items-center">
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Thermometer className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Current</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather.temperature.toFixed(1)}°C
                  </div>
                  <div className="text-xs text-primary-100">
                    Feels like {currentWeather.apparentTemp ? currentWeather.apparentTemp.toFixed(1) : currentWeather.temperature.toFixed(1)}°C
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Droplets className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Rain</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather.precipitation.toFixed(1)}mm
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Wind className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Wind</div>
                  <div className="text-lg font-semibold text-white">
                    {currentWeather.windSpeed ? currentWeather.windSpeed.toFixed(1) : '0.0'}km/h
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
              Temperature Trends
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
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
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
                  formatter={(value: number) => [`${value}°C`, 'Temperature']}
                  labelFormatter={(label: string) => new Date(label).toLocaleDateString()}
                />
                <Line type="monotone" dataKey="maxTemp" name="Max" stroke="#ef4444" dot={false} />
                <Line type="monotone" dataKey="minTemp" name="Min" stroke="#3b82f6" dot={false} />
                <Line type="monotone" dataKey="avgTemp" name="Avg" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="animate-slide-up [animation-delay:200ms]">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
              <Droplets className="h-5 w-5 text-primary-500" />
              Precipitation Analysis
            </h3>
            {climateTrends && (
              <div className="flex items-center gap-2 rounded-lg bg-primary-50 px-3 py-1 text-sm text-primary-600">
                <Gauge className="h-4 w-4" />
                Total: {climateTrends.rainfall.totalAccumulated.toFixed(0)}mm
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
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
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
                  formatter={(value: number) => [`${value}mm`, 'Precipitation']}
                  labelFormatter={(label: string) => new Date(label).toLocaleDateString()}
                />
                <Bar
                  dataKey="rainfall"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                  barSize={30}
                />
                <Line type="monotone" dataKey="rainProb" name="Probability" stroke="#8b5cf6" yAxisId="right" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {climateTrends && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="rounded-lg bg-white p-6 shadow-soft">
              <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                <Thermometer className="h-5 w-5 text-primary-500" />
                Temperature Analysis
              </h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Trend</span>
                  <div className="flex items-center gap-2">
                    {climateTrends.temperature.trend === 'rising' && <TrendingUp className="h-4 w-4 text-red-500" />}
                    {climateTrends.temperature.trend === 'falling' && <TrendingDown className="h-4 w-4 text-blue-500" />}
                    {climateTrends.temperature.trend === 'stable' && <Minus className="h-4 w-4 text-neutral-500" />}
                    <span className="font-medium capitalize">{climateTrends.temperature.trend}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Average</span>
                  <span className="font-medium">{climateTrends.temperature.average.toFixed(1)}°C</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Anomaly</span>
                  <span className={`font-medium ${climateTrends.temperature.anomaly > 0 ? 'text-red-500' :
                    climateTrends.temperature.anomaly < 0 ? 'text-blue-500' : 'text-neutral-500'
                    }`}>
                    {climateTrends.temperature.anomaly > 0 ? '+' : ''}{climateTrends.temperature.anomaly.toFixed(1)}°C
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-lg bg-white p-6 shadow-soft">
              <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                <Cloud className="h-5 w-5 text-primary-500" />
                Rainfall Analysis
              </h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Trend</span>
                  <div className="flex items-center gap-2">
                    {climateTrends.rainfall.trend === 'rising' && <TrendingUp className="h-4 w-4 text-blue-500" />}
                    {climateTrends.rainfall.trend === 'falling' && <TrendingDown className="h-4 w-4 text-orange-500" />}
                    {climateTrends.rainfall.trend === 'stable' && <Minus className="h-4 w-4 text-neutral-500" />}
                    <span className="font-medium capitalize">{climateTrends.rainfall.trend}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Total Accumulated</span>
                  <span className="font-medium">{climateTrends.rainfall.totalAccumulated.toFixed(1)}mm</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-neutral-50 p-4">
                  <span className="text-sm text-neutral-600">Days with Rain</span>
                  <span className="font-medium">{climateTrends.rainfall.daysWithRain} days</span>
                </div>
              </div>
            </div>

            <div className="col-span-1 md:col-span-2">
              <div className="rounded-lg bg-white p-6 shadow-soft">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-neutral-900">
                  <AlertTriangle className="h-5 w-5 text-primary-500" />
                  Extreme Events
                </h4>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">Hot Days</div>
                    <div className="mt-1 text-2xl font-semibold text-red-500">
                      {climateTrends.extremeEvents.hotDays}
                    </div>
                    <div className="text-xs text-neutral-500">Above 30°C</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">Cold Days</div>
                    <div className="mt-1 text-2xl font-semibold text-blue-500">
                      {climateTrends.extremeEvents.coldDays}
                    </div>
                    <div className="text-xs text-neutral-500">Below 15°C</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">Heavy Rain</div>
                    <div className="mt-1 text-2xl font-semibold text-blue-500">
                      {climateTrends.extremeEvents.heavyRainDays}
                    </div>
                    <div className="text-xs text-neutral-500">Above 30mm</div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-4">
                    <div className="text-sm text-neutral-600">Dry Days</div>
                    <div className="mt-1 text-2xl font-semibold text-orange-500">
                      {climateTrends.extremeEvents.dryDays}
                    </div>
                    <div className="text-xs text-neutral-500">No rain</div>
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
