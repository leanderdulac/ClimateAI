import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useEffect, useState } from 'react';
import { embrapaApi } from '@/lib/embrapaApi';
import { Sun, Droplets, Wind, Thermometer, Eye, Gauge } from 'lucide-react';

interface ClimateDataPoint {
  date: string;
  temp: number;
  rainfall: number;
}

export function ClimateDataWidget() {
  const [climateData, setClimateData] = useState<ClimateDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchClimateData = async () => {
      try {
        // For demo purposes, using a fixed location (São Paulo)
        // In a real app, this would come from the LocationSelector component
        const data = await embrapaApi.getClimateData(-23.5505, -46.6333, '2023-01-01', '2023-12-31');
        
        // Transform data for charts
        const chartData: ClimateDataPoint[] = data.map((item: any) => ({
          date: item.date,
          temp: item.temperature,
          rainfall: item.precipitation
        }));
        
        setClimateData(chartData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching climate data:', error);
        setLoading(false);
      }
    };

    fetchClimateData();
  }, []);

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

  // Calculate some summary stats for the overview
  const avgTemp = climateData.length ? climateData.reduce((sum, item) => sum + item.temp, 0) / climateData.length : 0;
  const totalRainfall = climateData.length ? climateData.reduce((sum, item) => sum + item.rainfall, 0) : 0;

  return (
    <Card className="overflow-hidden animate-fade-in" variant="default">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <Sun className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Climate Analytics</CardTitle>
              <CardDescription className="text-primary-100">
                Real-time climate patterns for São Paulo region
              </CardDescription>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:flex sm:items-center">
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Thermometer className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Avg. Temp</div>
                <div className="text-lg font-semibold text-white">{avgTemp.toFixed(1)}°C</div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-white/10 px-4 py-2">
              <Droplets className="h-5 w-5 text-primary-100" />
              <div>
                <div className="text-sm text-primary-100">Total Rain</div>
                <div className="text-lg font-semibold text-white">{totalRainfall.toFixed(0)}mm</div>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-8 p-6 bg-gradient-to-b from-white to-neutral-50">
        <div className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
              <Thermometer className="h-5 w-5 text-primary-500" />
              Temperature Trends
            </h3>
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <span className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-primary-500"></div>
                Daily
              </span>
              <span className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-primary-300"></div>
                Average
              </span>
            </div>
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
                  formatter={(value) => [`${value}°C`, 'Temperature']}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={{ stroke: '#0ea5e9', strokeWidth: 2, r: 3, fill: '#fff' }}
                  activeDot={{ stroke: '#0ea5e9', strokeWidth: 2, r: 5, fill: '#fff' }}
                />
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
            <div className="flex items-center gap-2 rounded-lg bg-primary-50 px-3 py-1 text-sm text-primary-600">
              <Gauge className="h-4 w-4" />
              Total: {totalRainfall.toFixed(0)}mm
            </div>
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
                  formatter={(value) => [`${value}mm`, 'Precipitation']}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Bar
                  dataKey="rainfall"
                  fill="#0ea5e9"
                  radius={[4, 4, 0, 0]}
                  barSize={30}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}