import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { hathorApi, type ClimateIndexRequest, type ClimateIndexResponse } from '@/lib/hathor';
import { 
  Cloud, 
  Thermometer, 
  CloudRain, 
  Wind, 
  Activity, 
  Database, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  TrendingUp,
  Calendar,
  MapPin,
  Server
} from "lucide-react";
import { useTranslation } from '@/hooks/useTranslation';

export function OraclePage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('index');
  
  // Climate Index State
  const [indexData, setIndexData] = useState<ClimateIndexRequest>({
    index_type: 'precipitation',
    latitude: -23.5505,
    longitude: -46.6333,
    start_date: '',
    end_date: '',
    trigger_value: 100,
    trigger_condition: 'below',
    source: 'noaa',
  });
  
  const [indexResult, setIndexResult] = useState<ClimateIndexResponse | null>(null);
  const [loadingIndex, setLoadingIndex] = useState(false);
  const [indexError, setIndexError] = useState('');
  
  // Cache Status State
  const [cacheStatus, setCacheStatus] = useState({
    enabled: false,
    hits: 0,
    misses: 0,
    hitRate: 0,
  });
  
  // Rate Limit Status
  const [rateLimitStatus, setRateLimitStatus] = useState({
    noaa: { remaining: 10000, limit: 10000, resetIn: 0 },
    openmeteo: { remaining: 100000, limit: 100000, resetIn: 0 },
  });
  
  // Data Sources
  const dataSources = [
    { id: 'noaa', name: 'NOAA CDO', status: 'active', latency: '~500ms', coverage: 'Global' },
    { id: 'openmeteo', name: 'OpenMeteo', status: 'active', latency: '~300ms', coverage: 'Global' },
    { id: 'inmet', name: 'INMET', status: 'inactive', latency: '~800ms', coverage: 'Brasil' },
  ];

  // Set default dates
  useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    setIndexData(prev => ({
      ...prev,
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    }));
  }, []);

  // Fetch cache and rate limit status (mock for now)
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        // In production, fetch from backend
        setCacheStatus({
          enabled: true,
          hits: 1247,
          misses: 389,
          hitRate: 76.2,
        });
        
        setRateLimitStatus({
          noaa: { remaining: 9856, limit: 10000, resetIn: 86400 },
          openmeteo: { remaining: 98234, limit: 100000, resetIn: 86400 },
        });
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Handle climate index fetch
  const handleFetchIndex = async () => {
    setLoadingIndex(true);
    setIndexError('');
    
    try {
      const response = await hathorApi.post<ClimateIndexResponse>('/oracle/index', indexData);
      setIndexResult(response.data);
    } catch (error: any) {
      setIndexError(error.response?.data?.detail || 'Erro ao buscar índice climático');
      console.error('Error fetching climate index:', error);
    } finally {
      setLoadingIndex(false);
    }
  };

  // Get icon for index type
  const getIndexIcon = (type: string) => {
    switch (type) {
      case 'precipitation':
        return <CloudRain className="h-6 w-6" />;
      case 'temperature':
        return <Thermometer className="h-6 w-6" />;
      case 'wind':
        return <Wind className="h-6 w-6" />;
      default:
        return <Activity className="h-6 w-6" />;
    }
  };

  return (
    <DashboardLayout
      title="Oracle & Backtesting"
      subtitle="Dados climáticos em tempo real, cache e rate limiting"
    >
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4">
          <TabsTrigger value="index" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Índice Climático
          </TabsTrigger>
          <TabsTrigger value="sources" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Fontes de Dados
          </TabsTrigger>
          <TabsTrigger value="cache" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            Cache
          </TabsTrigger>
          <TabsTrigger value="limits" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Rate Limits
          </TabsTrigger>
        </TabsList>

        {/* Tab: Climate Index */}
        <TabsContent value="index" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Input Form */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Buscar Índice Climático
                </CardTitle>
                <CardDescription>
                  Consulte dados históricos de fontes como NOAA e OpenMeteo
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Latitude</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={indexData.latitude}
                      onChange={(e) => setIndexData({ ...indexData, latitude: parseFloat(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label>Longitude</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={indexData.longitude}
                      onChange={(e) => setIndexData({ ...indexData, longitude: parseFloat(e.target.value) })}
                    />
                  </div>
                </div>

                <div>
                  <Label>Tipo de Índice</Label>
                  <Select
                    value={indexData.index_type}
                    onValueChange={(value) => setIndexData({ ...indexData, index_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="precipitation">Precipitação</SelectItem>
                      <SelectItem value="temperature">Temperatura</SelectItem>
                      <SelectItem value="wind">Vento</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Data Início</Label>
                    <Input
                      type="date"
                      value={indexData.start_date}
                      onChange={(e) => setIndexData({ ...indexData, start_date: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Data Fim</Label>
                    <Input
                      type="date"
                      value={indexData.end_date}
                      onChange={(e) => setIndexData({ ...indexData, end_date: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Trigger Value</Label>
                    <Input
                      type="number"
                      value={indexData.trigger_value}
                      onChange={(e) => setIndexData({ ...indexData, trigger_value: parseFloat(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label>Condição</Label>
                    <Select
                      value={indexData.trigger_condition}
                      onValueChange={(value) => setIndexData({ ...indexData, trigger_condition: value as 'above' | 'below' })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="above">Acima</SelectItem>
                        <SelectItem value="below">Abaixo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Fonte de Dados</Label>
                  <Select
                    value={indexData.source}
                    onValueChange={(value) => setIndexData({ ...indexData, source: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="noaa">NOAA (EUA)</SelectItem>
                      <SelectItem value="openmeteo">OpenMeteo (Global)</SelectItem>
                      <SelectItem value="inmet">INMET (Brasil)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {indexError && (
                  <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                    <AlertCircle className="h-5 w-5" />
                    <span className="text-sm">{indexError}</span>
                  </div>
                )}

                <Button 
                  onClick={handleFetchIndex} 
                  disabled={loadingIndex}
                  className="w-full"
                >
                  {loadingIndex ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Buscando...
                    </>
                  ) : (
                    <>
                      <CloudRain className="h-4 w-4 mr-2" />
                      Buscar Índice
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Resultado
                </CardTitle>
                <CardDescription>
                  Índice climático calculado e trigger verification
                </CardDescription>
              </CardHeader>
              <CardContent>
                {indexResult ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        {getIndexIcon(indexResult.index_type)}
                        <div>
                          <p className="font-semibold capitalize">{indexResult.index_type}</p>
                          <p className="text-sm text-muted-foreground">{indexResult.calculation_method}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-3xl font-bold">{indexResult.index_value.toFixed(1)}</p>
                        <p className="text-xs text-muted-foreground">
                          {indexResult.index_type === 'temperature' ? '°C' : 'mm'}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-muted-foreground mb-1">Trigger Value</p>
                        <p className="text-lg font-semibold">{indexResult.trigger_value}</p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {indexResult.trigger_condition === 'above' ? '≥' : '≤'}
                        </p>
                      </div>
                      <div className={`p-3 rounded-lg ${indexResult.trigger_met ? 'bg-green-50' : 'bg-red-50'}`}>
                        <p className="text-xs text-muted-foreground mb-1">Trigger Met</p>
                        <div className="flex items-center gap-2">
                          {indexResult.trigger_met ? (
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-red-600" />
                          )}
                          <p className={`text-lg font-semibold ${indexResult.trigger_met ? 'text-green-600' : 'text-red-600'}`}>
                            {indexResult.trigger_met ? 'SIM' : 'NÃO'}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-muted-foreground mb-1">Localização</p>
                        <div className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" />
                          <p className="text-sm font-medium">
                            {indexResult.latitude.toFixed(4)}, {indexResult.longitude.toFixed(4)}
                          </p>
                        </div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-muted-foreground mb-1">Período</p>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          <p className="text-sm font-medium">
                            {new Date(indexResult.start_date).toLocaleDateString('pt-BR')} - {new Date(indexResult.end_date).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Dados</p>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{indexResult.data_points_count} pontos de dados</span>
                        <Badge variant="outline">{indexResult.region}</Badge>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                    <CloudRain className="h-16 w-16 mb-4 opacity-20" />
                    <p className="text-sm">Nenhum índice buscado ainda</p>
                    <p className="text-xs">Preencha o formulário e clique em "Buscar Índice"</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Data Sources */}
        <TabsContent value="sources">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Fontes de Dados Climáticos
              </CardTitle>
              <CardDescription>
                APIs e serviços integrados para obtenção de dados históricos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                {dataSources.map((source) => (
                  <div
                    key={source.id}
                    className={`p-6 rounded-lg border-2 ${
                      source.status === 'active' 
                        ? 'border-green-200 bg-green-50' 
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold">{source.name}</h3>
                      <Badge variant={source.status === 'active' ? 'default' : 'secondary'}>
                        {source.status === 'active' ? 'Ativo' : 'Inativo'}
                      </Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Status:</span>
                        <span className={source.status === 'active' ? 'text-green-600' : 'text-gray-600'}>
                          {source.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Latência:</span>
                        <span>{source.latency}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Cobertura:</span>
                        <span>{source.coverage}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Detalhes das APIs
                </h4>
                <div className="grid gap-4 md:grid-cols-2 text-sm">
                  <div>
                    <p className="font-medium mb-1">NOAA CDO API</p>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Rate limit: 5 req/s, 10,000 req/dia</li>
                      <li>Dados desde 1800s (varia por estação)</li>
                      <li>Estações: ~150,000 globalmente</li>
                      <li>Dataset principal: GHCND (Daily)</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-1">OpenMeteo API</p>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Sem API key necessária</li>
                      <li>Dados desde 1940</li>
                      <li>Resolução: ~11km grade</li>
                      <li>Fallback automático</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Cache */}
        <TabsContent value="cache">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Status do Cache (Redis)
              </CardTitle>
              <CardDescription>
                Monitoramento de cache hits, misses e TTL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg">
                  <p className="text-sm opacity-80 mb-1">Cache Enabled</p>
                  <p className="text-4xl font-bold">{cacheStatus.enabled ? 'SIM' : 'NÃO'}</p>
                  <div className="mt-4 flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${cacheStatus.enabled ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`} />
                    <span className="text-sm">{cacheStatus.enabled ? 'Online' : 'Offline'}</span>
                  </div>
                </div>

                <div className="p-6 bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg">
                  <p className="text-sm opacity-80 mb-1">Cache Hits</p>
                  <p className="text-4xl font-bold">{cacheStatus.hits.toLocaleString()}</p>
                  <p className="text-sm opacity-80 mt-4">Requisições atendidas pelo cache</p>
                </div>

                <div className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg">
                  <p className="text-sm opacity-80 mb-1">Hit Rate</p>
                  <p className="text-4xl font-bold">{cacheStatus.hitRate.toFixed(1)}%</p>
                  <p className="text-sm opacity-80 mt-4">Eficiência do cache</p>
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-3">TTL Configuration</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Dados recentes (≤1 dia)</span>
                      <Badge variant="outline">1 hora</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Dados semanais (≤7 dias)</span>
                      <Badge variant="outline">24 horas</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Dados antigos (&gt;7 dias)</span>
                      <Badge variant="outline">7 dias</Badge>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-3">Cache Performance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Speedup médio</span>
                      <span className="font-medium">10-100x</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Redução de API calls</span>
                      <span className="font-medium">~80%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Economia de custos</span>
                      <span className="font-medium text-green-600">~80%</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Rate Limits */}
        <TabsContent value="limits">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5" />
                Rate Limiting Status
              </CardTitle>
              <CardDescription>
                Monitoramento de limites de requisições por API
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                {/* NOAA Rate Limit */}
                <div className="p-6 border rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <CloudRain className="h-5 w-5" />
                      NOAA API
                    </h3>
                    <Badge variant={rateLimitStatus.noaa.remaining > 1000 ? 'default' : 'destructive'}>
                      {rateLimitStatus.noaa.remaining > 1000 ? 'Normal' : 'Crítico'}
                    </Badge>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Requests restantes</span>
                      <span>{rateLimitStatus.noaa.remaining.toLocaleString()} / {rateLimitStatus.noaa.limit.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full transition-all ${
                          rateLimitStatus.noaa.remaining > 5000 ? 'bg-green-500' :
                          rateLimitStatus.noaa.remaining > 1000 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${(rateLimitStatus.noaa.remaining / rateLimitStatus.noaa.limit) * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="mt-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Limite por segundo:</span>
                      <span>5 req/s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Limite diário:</span>
                      <span>10,000 req/dia</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Reset em:</span>
                      <span>{Math.floor(rateLimitStatus.noaa.resetIn / 3600)}h {Math.floor((rateLimitStatus.noaa.resetIn % 3600) / 60)}m</span>
                    </div>
                  </div>
                </div>

                {/* OpenMeteo Rate Limit */}
                <div className="p-6 border rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <Cloud className="h-5 w-5" />
                      OpenMeteo API
                    </h3>
                    <Badge variant="default">Normal</Badge>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Requests restantes</span>
                      <span>{rateLimitStatus.openmeteo.remaining.toLocaleString()} / {rateLimitStatus.openmeteo.limit.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-green-500 h-3 rounded-full transition-all"
                        style={{ width: `${(rateLimitStatus.openmeteo.remaining / rateLimitStatus.openmeteo.limit) * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="mt-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Limite por segundo:</span>
                      <span>10 req/s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Limite diário:</span>
                      <span>100,000 req/dia</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Reset em:</span>
                      <span>{Math.floor(rateLimitStatus.openmeteo.resetIn / 3600)}h {Math.floor((rateLimitStatus.openmeteo.resetIn % 3600) / 60)}m</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Como Funciona o Rate Limiting
                </h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600" />
                    <span>Auto-throttling: requests são atrasados automaticamente para respeitar limites</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600" />
                    <span>Fallback automático: se NOAA atingir limite, usa OpenMeteo</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600" />
                    <span>Reset diário automático dos contadores</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600" />
                    <span>Logging de todos os eventos de rate limiting</span>
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
}
