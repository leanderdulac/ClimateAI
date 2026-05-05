/**
 * Atlas Dashboard Panel
 * Painel completo para monitoramento do Atlas Digital de Desastres
 * Integra: Dados climáticos reais, Oracle simulation, Blockchain e Risk analysis
 */

import React, { Suspense, lazy, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { buildApiUrl } from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertTriangle,
  ShieldAlert,
  TrendingUp,
  MapPin,
  DollarSign,
  Activity,
  CloudRain,
  Thermometer,
  Wind,
  Droplets,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Database,
  Server,
  Wifi,
  WifiOff,
  Newspaper
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from "@/hooks/useTranslation";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const GlobeVisualization = lazy(() =>
  import('./GlobeVisualization').then((module) => ({ default: module.GlobeVisualization }))
);

interface GlobeEvent {
  lat: number;
  lng: number;
  weight: number;
  type: string;
  title: string;
  description: string;
  date: string;
  location?: string;
  source?: string;
}

interface AtlasData {
  oracleStatus: any;
  portfolioRisk: any;
  liveEvents: any[];
  realtimeWeather: any[];
  riskSummary: any;
  spaceWeather: any;
  conjunctions: any;
}

interface NewsAlert {
  alert_id: string;
  title: string;
  summary: string;
  source: string;
  source_url: string;
  published: string;
  disaster_type: string;
  severity: string;
  severity_score: number;
  locations: string[];
  uf: string | null;
  confidence: number;
}

export function AtlasDashboardPanel() {
  const { t, language } = useTranslation();
  const [data, setData] = useState<AtlasData | null>(null);
  const [loading, setLoading] = useState(true);
  const [shouldRenderGlobe, setShouldRenderGlobe] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [newsAlerts, setNewsAlerts] = useState<NewsAlert[]>([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{
    backend: boolean;
    oracle: boolean;
    blockchain: boolean;
    weather: boolean;
    celestrak: boolean;
  }>({
    backend: false,
    oracle: false,
    blockchain: false,
    weather: false,
    celestrak: false,
  });

  const fetchData = async () => {
    try {
      setLoading(true);

      // Buscar dados de múltiplas fontes
      const [oracleRes, portfolioRes, eventsRes, weatherRes, riskRes, spaceWeatherRes, conjunctionsRes, allCitiesRes] = await Promise.allSettled([
        fetch(buildApiUrl('/api/v1/atlas-simulation/oracle-status')),
        fetch(buildApiUrl('/api/v1/atlas-simulation/portfolio-risk')),
        fetch(buildApiUrl('/api/v1/atlas-simulation/live-events?limit=10')),
        fetch(buildApiUrl('/api/v1/atlas-realtime/risk-summary')),
        fetch(buildApiUrl('/api/v1/atlas-integration/health')),
        fetch(buildApiUrl('/api/v1/celestrak/space-weather')),
        fetch(buildApiUrl('/api/v1/celestrak/conjunctions')),
        fetch(buildApiUrl('/api/v1/atlas-realtime/all-cities')),
      ]);

      const atlasData: Partial<AtlasData> = {};

      // Backend health
      if (riskRes.status === 'fulfilled' && riskRes.value.ok) {
        setConnectionStatus(prev => ({ ...prev, backend: true }));
      }

      if (oracleRes.status === 'fulfilled' && oracleRes.value.ok) {
        atlasData.oracleStatus = await oracleRes.value.json();
        setConnectionStatus(prev => ({ ...prev, oracle: true }));
      } else {
        console.warn('Oracle status failed:', oracleRes);
      }

      if (portfolioRes.status === 'fulfilled' && portfolioRes.value.ok) {
        atlasData.portfolioRisk = await portfolioRes.value.json();
        setConnectionStatus(prev => ({ ...prev, blockchain: true }));
      } else {
        console.warn('Portfolio risk failed:', portfolioRes);
      }

      if (eventsRes.status === 'fulfilled' && eventsRes.value.ok) {
        const events = await eventsRes.value.json();
        console.log('Live events loaded:', events?.length || 0);
        atlasData.liveEvents = events;
      } else {
        console.warn('Live events failed:', eventsRes);
        atlasData.liveEvents = [];
      }

      if (weatherRes.status === 'fulfilled' && weatherRes.value.ok) {
        atlasData.riskSummary = await weatherRes.value.json();
        setConnectionStatus(prev => ({ ...prev, weather: true }));
      } else {
        console.warn('Weather summary failed:', weatherRes);
      }

      // All cities weather data
      if (allCitiesRes.status === 'fulfilled' && allCitiesRes.value.ok) {
        const citiesJson = await allCitiesRes.value.json();
        atlasData.realtimeWeather = citiesJson.data || [];
        setConnectionStatus(prev => ({ ...prev, weather: true }));
      } else {
        console.warn('All cities weather failed:', allCitiesRes);
        atlasData.realtimeWeather = [];
      }

      // CelesTrak Data Processing
      let celestrakOnline = false;
      if (spaceWeatherRes.status === 'fulfilled' && spaceWeatherRes.value.ok) {
        atlasData.spaceWeather = await spaceWeatherRes.value.json();
        celestrakOnline = true;
      }
      if (conjunctionsRes.status === 'fulfilled' && conjunctionsRes.value.ok) {
        atlasData.conjunctions = await conjunctionsRes.value.json();
        celestrakOnline = true;
      }
      setConnectionStatus(prev => ({ ...prev, celestrak: celestrakOnline }));

      setData(atlasData as AtlasData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error(t('atlas.panel.error.fetching'), error);
      setData({
        oracleStatus: { total_events_processed: 0, total_payouts_triggered: 0 },
        portfolioRisk: { summary: { total_exposure: 0, potential_payout: 0, total_alerts: 0, high_severity_count: 0, impacted_policies_count: 0 } },
        liveEvents: [],
        realtimeWeather: [],
        riskSummary: null,
        spaceWeather: null,
        conjunctions: null,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh a cada minuto
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (val: number) => {
    return `${t('common.currency')} ${val.toLocaleString(language, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    })}`;
  };

  const getStatusColor = (status: boolean) => status ? 'text-green-600' : 'text-red-600';
  const getStatusIcon = (status: boolean) => status ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />;

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'low': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      default: return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  const getSeverityColor = (score: number) => {
    if (score >= 4.0) return 'text-red-600 font-bold';
    if (score >= 3.0) return 'text-amber-600 font-semibold';
    return 'text-emerald-600';
  };

  // Dados para gráficos
  const eventTypeData = data?.liveEvents?.reduce((acc: any, event: any) => {
    const type = event.disaster_type;
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {}) || {};

  const eventTypesChart = Object.entries(eventTypeData).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const severityData = data?.liveEvents?.map((event: any, idx: number) => ({
    name: `${idx + 1}`,
    severity: event.severity_score,
    payout: event.payout_triggered ? event.payout_amount : 0,
  })) || [];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  // Map live events to Globe objects
  const globeEvents: GlobeEvent[] = React.useMemo(() => {
    return data?.liveEvents?.filter(e => e.latitude && e.longitude).map((event: any) => ({
      lat: event.latitude,
      lng: event.longitude,
      weight: event.severity_score / 10,
      type: event.disaster_type,
      title: `${event.disaster_type.toUpperCase()} - Severity ${event.severity_score.toFixed(1)}`,
      description: event.description,
      date: event.timestamp,
      location: event.municipio ? `${event.municipio}/${event.uf || 'BR'}` : 'Brasil',
      source: event.source || (event.payout_triggered ? 'Oracle / Blockchain' : 'Atlas Simulation')
    })) || [];
  }, [data?.liveEvents]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-[600px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t('atlas.panel.title')}</h2>
          <p className="text-muted-foreground">
            {t('atlas.panel.description')}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            {t('atlas.panel.refresh')}
          </Button>
          <div className="text-sm text-muted-foreground">
            {t('atlas.panel.lastUpdate')}: {lastUpdate.toLocaleTimeString(language)}
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Server className="h-4 w-4" />
            {t('atlas.panel.connections')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            <div className="flex items-center gap-2">
              {getStatusIcon(connectionStatus.backend)}
              <span className={getStatusColor(connectionStatus.backend)}>Backend API</span>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(connectionStatus.oracle)}
              <span className={getStatusColor(connectionStatus.oracle)}>Oracle</span>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(connectionStatus.blockchain)}
              <span className={getStatusColor(connectionStatus.blockchain)}>Blockchain</span>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(connectionStatus.weather)}
              <span className={getStatusColor(connectionStatus.weather)}>Clima</span>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(connectionStatus.celestrak)}
              <span className={getStatusColor(connectionStatus.celestrak)}>CelesTrak API</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3D Globe Visualization */}
      <div className="w-full mb-8">
        {shouldRenderGlobe ? (
          <div className="space-y-3">
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setShouldRenderGlobe(false)}>
                Ocultar globo 3D
              </Button>
            </div>
            <Suspense fallback={<Skeleton className="h-[500px] w-full" />}>
              <GlobeVisualization events={globeEvents} height={500} />
            </Suspense>
          </div>
        ) : (
          <Card className="border-slate-200 bg-slate-50/80">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                Visualizacao 3D sob demanda
              </CardTitle>
              <CardDescription>
                O globo interativo foi isolado para nao carregar o bundle 3D pesado antes de ser necessario.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1 text-sm text-muted-foreground">
                <p>{globeEvents.length} eventos com coordenadas estao prontos para visualizacao.</p>
                <p>Carregue o globo apenas quando precisar explorar o mapa 3D.</p>
              </div>
              <Button
                onClick={() => {
                  React.startTransition(() => setShouldRenderGlobe(true));
                }}
                disabled={globeEvents.length === 0}
              >
                Carregar globo 3D
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-red-100 bg-red-50/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-red-600" />
              {t('atlas.kpi.exposure')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">
              {formatCurrency(data?.portfolioRisk?.summary?.total_exposure || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t('atlas.kpi.exposureDesc')}
            </p>
          </CardContent>
        </Card>

        <Card className="border-amber-100 bg-amber-50/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-amber-600" />
              {t('atlas.kpi.payout')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-700">
              {formatCurrency(data?.portfolioRisk?.summary?.potential_payout || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t('atlas.kpi.payoutDesc', { count: data?.portfolioRisk?.summary?.impacted_policies_count || 0 })}
            </p>
          </CardContent>
        </Card>

        <Card className="border-blue-100 bg-blue-50/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-600" />
              {t('atlas.kpi.activeEvents')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-700">
              {data?.portfolioRisk?.summary?.total_alerts || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t('atlas.kpi.activeEventsDesc', { count: data?.portfolioRisk?.summary?.high_severity_count || 0 })}
            </p>
          </CardContent>
        </Card>

        <Card className="border-emerald-100 bg-emerald-50/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4 text-emerald-600" />
              {t('atlas.kpi.oracleStatus')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-700">
              {data?.oracleStatus?.total_events_processed || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t('atlas.kpi.oracleStatusDesc', { count: data?.oracleStatus?.total_payouts_triggered || 0 })}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="events" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="events">{t('atlas.tabs.events')}</TabsTrigger>
          <TabsTrigger value="analytics">{t('atlas.tabs.analytics')}</TabsTrigger>
          <TabsTrigger value="weather">{t('atlas.tabs.weather')}</TabsTrigger>
          <TabsTrigger value="space">{t('atlas.tabs.space')}</TabsTrigger>
          <TabsTrigger value="blockchain">{t('atlas.tabs.blockchain')}</TabsTrigger>
          <TabsTrigger value="news">📰 Radar de Notícias</TabsTrigger>
        </TabsList>

        {/* Live Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                {t('atlas.events.title')}
              </CardTitle>
              <CardDescription>
                {t('atlas.events.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data?.liveEvents?.slice(0, 10).map((event, idx) => (
                  <div
                    key={event.event_id || idx}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${event.payout_triggered ? 'bg-red-100' : 'bg-blue-100'}`}>
                        {event.payout_triggered ? (
                          <ShieldAlert className="h-4 w-4 text-red-600" />
                        ) : (
                          <CloudRain className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                      <div>
                        <div className="font-semibold">
                          {event.municipio}/{event.uf}
                        </div>
                        <div className="text-sm text-muted-foreground capitalize">
                          {event.disaster_type}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-semibold ${getSeverityColor(event.severity_score)}`}>
                        {t('atlas.events.severity', { score: event.severity_score.toFixed(2) })}
                      </div>
                      {event.payout_triggered ? (
                        <div className="text-sm text-red-600 font-semibold">
                          {t('atlas.events.payout', { amount: formatCurrency(event.payout_amount) })}
                        </div>
                      ) : (
                        <div className="text-sm text-emerald-600">
                          {t('atlas.events.noPayout')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>{t('atlas.analytics.distribution')}</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={eventTypesChart}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {eventTypesChart.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('atlas.analytics.severityVsPayout')}</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="severity" fill="#8884d8" name={t('audit.risk.severity')} />
                    <Bar yAxisId="right" dataKey="payout" fill="#82ca9d" name={t('atlas.blockchain.payout')} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t('atlas.analytics.evolution')}</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 5]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="severity" stroke="#8884d8" strokeWidth={2} name="Severidade" />
                  <Line type="monotone" dataKey="payout" stroke="#82ca9d" strokeWidth={2} name="Payout" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Weather Tab */}
        <TabsContent value="weather" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CloudRain className="h-5 w-5" />
                {t('atlas.weather.title')}
              </CardTitle>
              <CardDescription>
                {t('atlas.weather.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <Wifi className="h-4 w-4" />
                <AlertTitle>{t('atlas.weather.dataSource')}</AlertTitle>
                <AlertDescription>
                  {t('atlas.weather.sourceDesc')}
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                {(() => {
                  const cityDisplayNames: Record<string, string> = {
                    sao_paulo: 'São Paulo',
                    rio_de_janeiro: 'Rio de Janeiro',
                    porto_alegre: 'Porto Alegre',
                    curitiba: 'Curitiba',
                    florianopolis: 'Florianópolis',
                    belo_horizonte: 'Belo Horizonte',
                    salvador: 'Salvador',
                    recife: 'Recife',
                    fortaleza: 'Fortaleza',
                    manaus: 'Manaus',
                    brasilia: 'Brasília',
                  };
                  const weatherList = data?.realtimeWeather || [];
                  if (weatherList.length === 0) {
                    return ['São Paulo', 'Rio de Janeiro', 'Porto Alegre', 'Curitiba', 'Florianópolis', 'Belo Horizonte'].map((city) => (
                      <Card key={city}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium">{city}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{t('weather.temp')}</span>
                            <div className="flex items-center gap-1">
                              <Thermometer className="h-3 w-3" />
                              <span className="text-sm font-semibold">--°C</span>
                            </div>
                          </div>
                          <Badge className="w-full justify-center mt-2">{t('common.loading')}</Badge>
                        </CardContent>
                      </Card>
                    ));
                  }
                  return weatherList.map((w: any) => {
                    const displayName = cityDisplayNames[w.city] || w.city;
                    const current = w.current || {};
                    const risk = w.risk_indicators || {};
                    return (
                      <Card key={w.city} className={risk.risk_level === 'HIGH' ? 'border-red-200 bg-red-50/30' : risk.risk_level === 'MEDIUM' ? 'border-amber-200 bg-amber-50/20' : ''}>
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-sm font-medium">{displayName}</CardTitle>
                            <Badge variant={risk.risk_level === 'HIGH' ? 'danger' : risk.risk_level === 'MEDIUM' ? 'secondary' : 'outline'} className="text-xs">
                              {risk.risk_level || 'N/A'}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{t('weather.temp')}</span>
                            <div className="flex items-center gap-1">
                              <Thermometer className="h-3 w-3" />
                              <span className="text-sm font-semibold">{current.temperature?.toFixed(1) ?? '--'}°C</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{t('weather.humidity')}</span>
                            <div className="flex items-center gap-1">
                              <Droplets className="h-3 w-3" />
                              <span className="text-sm font-semibold">{current.humidity?.toFixed(0) ?? '--'}%</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{t('weather.wind')}</span>
                            <div className="flex items-center gap-1">
                              <Wind className="h-3 w-3" />
                              <span className="text-sm font-semibold">{current.wind_speed?.toFixed(1) ?? '--'} km/h</span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{t('weather.rain')}</span>
                            <div className="flex items-center gap-1">
                              <CloudRain className="h-3 w-3" />
                              <span className="text-sm font-semibold">{current.precipitation?.toFixed(1) ?? '0.0'} mm</span>
                            </div>
                          </div>
                          <Badge variant="outline" className="w-full justify-center mt-2 text-xs">
                            {current.weather_description || w.source || 'OpenMeteo'}
                          </Badge>
                        </CardContent>
                      </Card>
                    );
                  });
                })()}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Space Weather (CelesTrak) Tab */}
        <TabsContent value="space" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-indigo-600" />
                  {t('atlas.space.title')}
                </CardTitle>
                <CardDescription>
                  {t('atlas.space.description')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {data?.spaceWeather ? (
                    <>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold text-lg">{t('atlas.space.kpIndex')}</span>
                          <Badge variant={data.spaceWeather.geomagnetic_storm_active ? "danger" : "outline"} className={data.spaceWeather.geomagnetic_storm_active ? "bg-red-500" : "bg-emerald-100 text-emerald-800"}>
                            {data.spaceWeather.kp_index} - {data.spaceWeather.geomagnetic_storm_active ? t('atlas.space.storm') : t('atlas.space.stable')}
                          </Badge>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${data.spaceWeather.geomagnetic_storm_active ? "bg-red-500" : "bg-emerald-500"}`}
                            style={{ width: `${Math.min((data.spaceWeather.kp_index / 9) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 border rounded-md">
                          <div className="text-sm text-muted-foreground">{t('atlas.space.solarFlux')}</div>
                          <div className="text-2xl font-bold">{data.spaceWeather.solar_flux ?? '--'}</div>
                        </div>
                        <div className="p-4 border rounded-md">
                          <div className="text-sm text-muted-foreground">{t('atlas.space.currentStatus')}</div>
                          <div className="text-lg font-bold">{data.spaceWeather.status ?? 'Normal'}</div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {t('atlas.space.lastReading', { time: new Date(data.spaceWeather.timestamp).toLocaleString(language) })}
                      </div>
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                      <WifiOff className="h-8 w-8 mb-2 opacity-50" />
                      <p>{t('atlas.space.unavailable')}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                  {t('atlas.conjunctions.title')}
                </CardTitle>
                <CardDescription>
                  {t('atlas.conjunctions.description')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {data?.conjunctions && data.conjunctions.alerts?.length > 0 ? (
                  <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    {data.conjunctions.alerts.slice(0, 5).map((alert: any, idx: number) => (
                      <div key={idx} className="p-3 border rounded-lg bg-slate-50 relative overflow-hidden">
                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${alert.miss_distance_km < 1.0 ? 'bg-red-500' : 'bg-amber-500'
                          }`} />
                        <div className="font-semibold text-sm mb-1">{alert.satellite_1} vs {alert.satellite_2}</div>
                        <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                          <div>
                            <span className="text-muted-foreground text-xs block">{t('atlas.conjunctions.minDistance')}</span>
                            <span className="font-mono">{alert.miss_distance_km} km</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground text-xs block">{t('atlas.conjunctions.probability')}</span>
                            <span className="font-mono text-red-600 font-medium">{alert.probability}</span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-muted-foreground text-xs block">{t('atlas.conjunctions.tcaTime')}</span>
                            <span className="font-mono text-xs">{new Date(alert.tca_time).toLocaleString(language)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                    <CheckCircle className="h-8 w-8 mb-2 text-emerald-500 opacity-50" />
                    <p>{t('atlas.conjunctions.noAlerts')}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Blockchain Tab */}
        <TabsContent value="blockchain" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                {t('atlas.blockchain.title')}
              </CardTitle>
              <CardDescription>
                {t('atlas.blockchain.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data?.portfolioRisk?.blockchain_transactions?.slice(0, 5).map((tx: any, idx: number) => (
                  <div
                    key={tx.tx_id || idx}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="font-mono text-sm">
                          {tx.tx_id?.substring(0, 16)}...
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {t('atlas.blockchain.confirmations', { count: tx.confirmations })}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-green-600">
                        {formatCurrency(tx.amount)}
                      </div>
                      <Badge variant="outline" className="mt-1">
                        {t('atlas.blockchain.confirmed')}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-4 mt-6">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {data?.oracleStatus?.total_blockchain_transactions || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {t('atlas.blockchain.totalTransactions')}
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        Hathor Testnet
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {t('atlas.blockchain.network')}
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        SIMULATION
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {t('atlas.blockchain.operationMode')}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* News Radar Tab */}
        <TabsContent value="news" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="h-5 w-5 text-purple-600" />
                Radar de Notícias em Tempo Real
              </CardTitle>
              <CardDescription>
                Notícias de desastres climáticos coletadas automaticamente via RSS de portais brasileiros
              </CardDescription>
              <Button
                variant="outline"
                size="sm"
                className="w-fit"
                onClick={async () => {
                  setNewsLoading(true);
                  try {
                    const res = await fetch(buildApiUrl('/api/v1/news-crawler/refresh'), { method: 'POST' });
                    if (res.ok) {
                      const alertsRes = await fetch(buildApiUrl('/api/v1/news-crawler/alerts?limit=20'));
                      if (alertsRes.ok) {
                        const json = await alertsRes.json();
                        setNewsAlerts(json.alerts || []);
                      }
                    }
                  } catch (e) { console.error(e); }
                  setNewsLoading(false);
                }}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${newsLoading ? 'animate-spin' : ''}`} />
                Atualizar Feeds
              </Button>
            </CardHeader>
            <CardContent>
              {newsAlerts.length === 0 && !newsLoading && (
                <div className="text-center py-8 text-muted-foreground">
                  <Newspaper className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Nenhum alerta detectado ainda.</p>
                  <p className="text-sm">Clique em "Atualizar Feeds" para coletar notícias dos portais.</p>
                </div>
              )}
              {newsLoading && (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-20 w-full" />)}
                </div>
              )}
              <div className="space-y-3">
                {newsAlerts.map((alert, idx) => {
                  const severityColors: Record<string, string> = {
                    'critica': 'bg-red-100 text-red-800 border-red-300',
                    'alta': 'bg-orange-100 text-orange-800 border-orange-300',
                    'media': 'bg-yellow-100 text-yellow-800 border-yellow-300',
                    'baixa': 'bg-blue-100 text-blue-800 border-blue-300',
                  };
                  const typeIcons: Record<string, string> = {
                    'inundacao': '🌊',
                    'deslizamento': '⛰️',
                    'vendaval': '🌪️',
                    'seca': '☀️',
                    'granizo': '🧊',
                    'incendio': '🔥',
                  };
                  return (
                    <div key={alert.alert_id || idx} className={`p-4 rounded-lg border ${severityColors[alert.severity] || 'bg-gray-50 border-gray-200'}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{typeIcons[alert.disaster_type] || '⚠️'}</span>
                            <Badge variant="outline" className="text-xs">
                              {alert.disaster_type?.replace('_', ' ')}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {alert.severity} ({alert.severity_score?.toFixed(1)})
                            </Badge>
                            {alert.uf && (
                              <Badge variant="outline" className="text-xs">
                                {alert.uf}
                              </Badge>
                            )}
                          </div>
                          <a href={alert.source_url} target="_blank" rel="noreferrer" className="font-medium text-sm hover:underline">
                            {alert.title}
                          </a>
                          {alert.summary && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{alert.summary}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span>📡 {alert.source}</span>
                            {alert.locations?.length > 0 && (
                              <span>📍 {alert.locations.join(', ')}</span>
                            )}
                            <span>🕐 {new Date(alert.published).toLocaleString('pt-BR')}</span>
                            <span>🎯 Confiança: {(alert.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Info Footer */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start gap-2">
              <Database className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <div className="font-semibold">Dados Históricos</div>
                <div className="text-muted-foreground">
                  Atlas Digital de Desastres 1991-2024 (MDR)
                </div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Activity className="h-4 w-4 text-amber-600 mt-0.5" />
              <div>
                <div className="font-semibold">Oracle em Tempo Real</div>
                <div className="text-muted-foreground">
                  Severity scoring automático com triggers de payout
                </div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <ShieldAlert className="h-4 w-4 text-red-600 mt-0.5" />
              <div>
                <div className="font-semibold">Blockchain Simulation</div>
                <div className="text-muted-foreground">
                  Hathor Testnet com smart contracts de payout
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
