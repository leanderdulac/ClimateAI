/**
 * Weather Widget Component
 * Displays current weather and forecast data from EMBRAPA API
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useEffect, useState } from 'react';
import { embrapaApi } from '@/lib/embrapaApi';
import { useLocation } from '@/lib/LocationContext';
import { Sun, Droplets, Wind, Thermometer } from 'lucide-react';

interface ClimateDataPoint {
  date: string;
  temperature: number;
  precipitation: number;
  humidity: number;
  windSpeed?: number;
  cloudCover?: number;
}

export function WeatherWidget() {
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

  const { selectedLocation, isLoadingLocation } = useLocation();

  const getWeatherDescription = (temperature: number, humidity: number, precipitation: number) => {
    if (precipitation > 5) return 'Chuva';
    if (humidity > 80) return 'Úmido';
    if (temperature > 30) return 'Quente';
    if (temperature < 15) return 'Frio';
    return 'Estável';
  };

  useEffect(() => {
    const fetchClimateData = async () => {
      try {
        console.log('WeatherWidget: Iniciando busca de dados climáticos...');

        let latitude: number;
        let longitude: number;
        let locationName: string;

        if (selectedLocation) {
          // Usar localização selecionada
          latitude = selectedLocation.latitude;
          longitude = selectedLocation.longitude;
          locationName = `${selectedLocation.cidade || 'Localização'}, ${selectedLocation.estado || ''}`;
          console.log('WeatherWidget: Usando localização selecionada:', locationName);
        } else {
          // Fallback para São Paulo
          latitude = -23.5505;
          longitude = -46.6333;
          locationName = 'São Paulo, SP';
          console.log('WeatherWidget: Usando localização padrão (São Paulo)');
        }

        // Buscar dados históricos de 30 anos (Embrapa)
        console.log('WeatherWidget: Buscando dados históricos de 30 anos...');
        setLoadingHistorical(true);
        try {
          const endDate = new Date();
          const startDate = new Date();
          startDate.setFullYear(startDate.getFullYear() - 30);

          const historical = await embrapaApi.getClimateData(
            latitude,
            longitude,
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0]
          );
          console.log('WeatherWidget: Dados históricos recebidos:', historical);
          setHistoricalData(historical || []);
        } catch (historicalError) {
          console.warn('WeatherWidget: Não foi possível obter dados históricos:', historicalError);
          setHistoricalData([]);
        } finally {
          setLoadingHistorical(false);
        }

        // Buscar previsão atual (OpenMeteo)
        console.log('WeatherWidget: Buscando previsão atual...');
        const currentData = await embrapaApi.getWeatherForecast(latitude, longitude, 1);
        console.log('WeatherWidget: Dados atuais recebidos:', currentData);

        if (currentData.length > 0) {
          // Adaptar formato dos dados do backend para o formato esperado pelo frontend
          const current = currentData[0];
          setCurrentWeather({
            temperature: current.temperature || current.temperatura_max || 20,
            humidity: current.humidity || 60,
            precipitation: current.precipitation || current.precipitacao || 0,
            windSpeed: current.windSpeed || current.vento_velocidade
          });
        }

        console.log('WeatherWidget: Buscando previsão para 7 dias...');
        // Busca previsão para os próximos dias
        const forecastData = await embrapaApi.getWeatherForecast(latitude, longitude, 7);
        console.log('WeatherWidget: Dados de previsão recebidos:', forecastData);

        // Adaptar formato dos dados
        const adaptedData: ClimateDataPoint[] = forecastData.map(item => ({
          date: item.date || item.data,
          temperature: item.temperature || item.temperatura_max || 20,
          precipitation: item.precipitation || item.precipitacao || 0,
          humidity: item.humidity || 60,
          windSpeed: item.windSpeed || item.vento_velocidade,
          cloudCover: item.cloudCover || 0
        }));

        setClimateData(adaptedData);
        setLoading(false);
        console.log('WeatherWidget: Dados carregados com sucesso');
      } catch (error) {
        console.error('WeatherWidget: Erro ao buscar dados climáticos:', error);
        setLoading(false);
        setLoadingHistorical(false);
      }
    };

    // Buscar dados quando o componente monta ou quando a localização muda
    if (!isLoadingLocation) {
      fetchClimateData();
    }
  }, [selectedLocation, isLoadingLocation]);

  if (loading || isLoadingLocation) {
    return (
      <Card className="overflow-hidden">
        <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Previsão do Tempo</CardTitle>
              <CardDescription className="text-primary-100">
                {isLoadingLocation ? 'Carregando localização...' : 'Carregando dados meteorológicos...'}
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
            <CardTitle className="text-xl font-bold text-white">
              {selectedLocation ? `${selectedLocation.cidade}, ${selectedLocation.estado}` : 'Previsão do Tempo'}
            </CardTitle>
            <CardDescription className="text-primary-100">
              {currentWeather ? `${getWeatherDescription(
                currentWeather.temperature,
                currentWeather.humidity,
                currentWeather.precipitation
              )} • ${historicalData.length > 0 ? `${historicalData.length} anos de dados históricos` : 'Dados históricos indisponíveis'}` : 'Carregando...'}
              {loadingHistorical && ' • Carregando dados históricos...'}
            </CardDescription>
          </div>
        </div>
        {currentWeather && (
          <div className="grid grid-cols-2 gap-4 sm:flex sm:items-center mt-4">
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Thermometer className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Temperatura</div>
                <div className="text-lg font-semibold text-white">
                  {currentWeather.temperature.toFixed(1)}°C
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Droplets className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Chuva</div>
                <div className="text-lg font-semibold text-white">
                  {currentWeather.precipitation.toFixed(1)}mm
                </div>
              </div>
            </div>
            {currentWeather.windSpeed && (
              <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
                <Wind className="h-5 w-5 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Vento</div>
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
          <h3 className="mb-4 text-lg font-semibold">Temperatura ao Longo do Tempo</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={climateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString()}
              />
              <YAxis unit="°C" />
              <Tooltip
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
                formatter={(value: any) => [value.toFixed(1) + "°C", "Temperatura"]}
              />
              <Line
                type="monotone"
                dataKey="temperature"
                name="Temperatura"
                stroke="#10b981"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h3 className="mb-4 text-lg font-semibold">Precipitação</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={climateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString()}
              />
              <YAxis unit="mm" />
              <Tooltip
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
                formatter={(value: any) => [value.toFixed(1) + "mm", "Precipitação"]}
              />
              <Bar
                dataKey="precipitation"
                name="Precipitação"
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
