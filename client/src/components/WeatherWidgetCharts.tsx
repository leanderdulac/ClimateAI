import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useTranslation } from '@/hooks/useTranslation';

export interface WeatherChartPoint {
  date: string;
  temperature: number;
  precipitation: number;
}

interface WeatherWidgetChartsProps {
  climateData: WeatherChartPoint[];
}

export function WeatherWidgetCharts({ climateData }: WeatherWidgetChartsProps) {
  const { t } = useTranslation();
  const locale = t('locale') || 'pt-BR';

  const formatDate = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(locale);
  };

  const formatTemperature = (value: number | string) => {
    const numericValue = typeof value === 'number' ? value : Number(value);
    return [`${numericValue.toFixed(1)}°C`, t('weather.temperature')];
  };

  const formatRain = (value: number | string) => {
    const numericValue = typeof value === 'number' ? value : Number(value);
    return [`${numericValue.toFixed(1)}mm`, t('weather.rain')];
  };

  return (
    <>
      <div>
        <h3 className="mb-4 text-lg font-semibold">{t('weather.temperatureOverTime')}</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={climateData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={formatDate} />
            <YAxis unit="°C" />
            <Tooltip labelFormatter={formatDate} formatter={formatTemperature} />
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
            <XAxis dataKey="date" tickFormatter={formatDate} />
            <YAxis unit="mm" />
            <Tooltip labelFormatter={formatDate} formatter={formatRain} />
            <Bar
              dataKey="precipitation"
              name={t('weather.rain')}
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}