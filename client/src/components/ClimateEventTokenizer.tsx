import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Zap, Package, TrendingUp, AlertTriangle, Thermometer, MapPin, Calendar, DollarSign, Loader2, Locate, Search, ChevronDown, ChevronUp } from "lucide-react";
import { useLocation } from '@/lib/LocationContext';
import { useTokenizationStore } from '@/store/useTokenizationStore';
import { embrapaApi } from '@/lib/api';
import type { LocalizacaoData } from '@/lib/api';
import { useTranslation } from '@/hooks/useTranslation';
import {
  isWithinBrazil,
  formatCoordinates,
  saveRecentLocation,
  getRecentLocations,
  type SavedLocation
} from '@/lib/geoUtils';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1/blockchain';

// Helper: format current datetime for <input type="datetime-local">
function getCurrentDateTimeLocal(): string {
  const now = new Date();
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

export function ClimateEventTokenizer() {
  const { t, language } = useTranslation();
  const [formData, setFormData] = useState({
    tipo: '',
    latitude: '',
    longitude: '',
    data_inicio: getCurrentDateTimeLocal(),
    intensidade: '',
    probabilidade: '',
    descricao: '',
    nivel_alerta: '',
    wallet_address: 'climatewise_wallet_test',
    token_supply: 10000,
    decimals: 0,
    risk_factors: undefined as Record<string, number> | undefined
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  // --- Location Integration State ---
  const { selectedLocation } = useLocation();
  const [locationName, setLocationName] = useState<string>('');
  const [locLoading, setLocLoading] = useState(false);
  const [locError, setLocError] = useState<string | null>(null);
  const [citySearch, setCitySearch] = useState('');
  const [stateSearch, setStateSearch] = useState('');
  const [showManualCoords, setShowManualCoords] = useState(false);
  const [recentLocations, setRecentLocations] = useState<SavedLocation[]>([]);
  const [citySuggestions, setCitySuggestions] = useState<LocalizacaoData[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    const recent = getRecentLocations();
    setRecentLocations(recent);
    // Auto-load the most recent location so preview is never blank
    if (recent.length > 0 && !formData.latitude && !formData.longitude) {
      const last = recent[0];
      applyLocation(last.latitude, last.longitude, last.name);
      setCitySearch(last.name?.split(',')[0]?.trim() || '');
      setStateSearch(last.state || '');
    }
  }, []);

  const { pendingTokenizationData, clearPendingTokenizationData } = useTokenizationStore();

  useEffect(() => {
    if (pendingTokenizationData) {
      setFormData(prev => ({
        ...prev,
        tipo: pendingTokenizationData.tipo,
        latitude: pendingTokenizationData.latitude,
        longitude: pendingTokenizationData.longitude,
        intensidade: pendingTokenizationData.intensidade,
        probabilidade: pendingTokenizationData.probabilidade,
        descricao: pendingTokenizationData.descricao,
        nivel_alerta: pendingTokenizationData.nivel_alerta,
        token_supply: pendingTokenizationData.token_supply,
        risk_factors: pendingTokenizationData.riskFactors
      }));

      applyLocation(
        parseFloat(pendingTokenizationData.latitude),
        parseFloat(pendingTokenizationData.longitude)
      );

      clearPendingTokenizationData();
    }
  }, [pendingTokenizationData, clearPendingTokenizationData]);

  // Sync from global LocationContext if it changes (e.g. dashboard sets it)
  useEffect(() => {
    if (selectedLocation) {
      applyLocation(selectedLocation.latitude, selectedLocation.longitude, selectedLocation.cidade
        ? `${selectedLocation.cidade}, ${selectedLocation.estado}`
        : undefined
      );
    }
  }, [selectedLocation]);

  // Auto-search: when both city + state are filled, trigger search after a debounce
  useEffect(() => {
    if (citySearch.length >= 3 && stateSearch.length === 2) {
      const timer = setTimeout(async () => {
        try {
          const data = await embrapaApi.getLocalizacaoPorCidade(citySearch, stateSearch);
          if (data.latitude && data.longitude) {
            applyLocation(data.latitude, data.longitude, `${data.cidade || citySearch}, ${data.estado || stateSearch}`);
            saveRecentLocation({ latitude: data.latitude, longitude: data.longitude, name: `${data.cidade || citySearch}, ${data.estado || stateSearch}`, state: data.estado, timestamp: Date.now() });
            setRecentLocations(getRecentLocations());
          }
        } catch {
          // Silent — user can still click the button
        }
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [citySearch, stateSearch]);

  const applyLocation = (lat: number, lon: number, name?: string) => {
    setFormData(prev => ({
      ...prev,
      latitude: lat.toString(),
      longitude: lon.toString()
    }));
    setLocationName(name || formatCoordinates(lat, lon));
    setLocError(null);
  };

  // GPS Detection
  const detectGPS = () => {
    setLocLoading(true);
    setLocError(null);
    if (!navigator.geolocation) {
      setLocError(t('location.errors.geolocation'));
      setLocLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        if (!isWithinBrazil(latitude, longitude)) {
          setLocError(t('location.errors.outside'));
          setLocLoading(false);
          return;
        }
        try {
          const data = await embrapaApi.getLocalizacao(latitude, longitude);
          const name = data.cidade ? `${data.cidade}, ${data.estado}` : undefined;
          applyLocation(latitude, longitude, name);
          saveRecentLocation({ latitude, longitude, name: name || formatCoordinates(latitude, longitude), state: data.estado, timestamp: Date.now() });
          setRecentLocations(getRecentLocations());
        } catch {
          applyLocation(latitude, longitude);
        }
        setLocLoading(false);
      },
      (err) => {
        setLocError(`${t('location.errors.geoFail')}: ${err.message}`);
        setLocLoading(false);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  };

  // City search suggestions
  const handleCityInput = async (term: string) => {
    setCitySearch(term);
    if (term.length < 2) { setCitySuggestions([]); setShowSuggestions(false); return; }
    try {
      const suggestions = await embrapaApi.buscarCidades(term);
      setCitySuggestions(suggestions);
      setShowSuggestions(suggestions.length > 0);
    } catch { setCitySuggestions([]); setShowSuggestions(false); }
  };

  const selectSuggestion = (s: LocalizacaoData) => {
    setCitySearch(s.cidade || '');
    setStateSearch(s.estado || '');
    setCitySuggestions([]);
    setShowSuggestions(false);
    applyLocation(s.latitude, s.longitude, `${s.cidade}, ${s.estado}`);
    saveRecentLocation({ latitude: s.latitude, longitude: s.longitude, name: `${s.cidade}, ${s.estado}`, state: s.estado, timestamp: Date.now() });
    setRecentLocations(getRecentLocations());
  };

  // Search by city + state
  const searchByCity = async () => {
    if (!citySearch || !stateSearch) { setLocError(t('location.errors.cityState')); return; }
    setLocLoading(true); setLocError(null);
    try {
      const data = await embrapaApi.getLocalizacaoPorCidade(citySearch, stateSearch);
      applyLocation(data.latitude, data.longitude, `${data.cidade || citySearch}, ${data.estado || stateSearch}`);
      saveRecentLocation({ latitude: data.latitude, longitude: data.longitude, name: `${data.cidade || citySearch}, ${data.estado || stateSearch}`, state: data.estado, timestamp: Date.now() });
      setRecentLocations(getRecentLocations());
    } catch { setLocError(t('location.errors.cityNotFound')); }
    setLocLoading(false);
  };

  // Select recent
  const selectRecent = (loc: SavedLocation) => {
    applyLocation(loc.latitude, loc.longitude, loc.name);
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCreateToken = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      if (!formData.tipo || !formData.latitude || !formData.longitude || !formData.data_inicio ||
        !formData.intensidade || !formData.probabilidade || !formData.descricao || !formData.nivel_alerta) {
        throw new Error(t('auth.errors.fillAll'));
      }

      const eventoData = {
        tipo: formData.tipo,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        data_inicio: new Date(formData.data_inicio).toISOString(),
        intensidade: parseFloat(formData.intensidade),
        probabilidade: parseFloat(formData.probabilidade) / 100,
        descricao: formData.descricao,
        nivel_alerta: parseInt(formData.nivel_alerta)
      };

      const tokenData = {
        evento: eventoData,
        wallet_address: formData.wallet_address,
        token_supply: formData.token_supply,
        decimals: formData.decimals,
        metadata: {
          created_at: new Date().toISOString(),
          creator: 'ClimateWise Dashboard',
          risk_factors: formData.risk_factors
        }
      };

      const response = await axios.post(`${API_BASE_URL}/mint`, tokenData, {
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.data.success) {
        setSuccess(true);
        setFormData({
          tipo: '', latitude: '', longitude: '', data_inicio: getCurrentDateTimeLocal(), intensidade: '',
          probabilidade: '', descricao: '', nivel_alerta: '', wallet_address: 'climatewise_wallet_test',
          token_supply: 10000, decimals: 0, risk_factors: undefined
        });
        setLocationName('');
      } else {
        throw new Error(response.data.error || t('tokenization.create.error.title'));
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || error.message || t('tokenization.create.error.title'));
    } finally {
      setLoading(false);
    }
  };

  const getEventTypeIcon = (tipo: string) => {
    const icons = {
      'enchente': <Zap className="h-4 w-4 text-blue-600" />,
      'seca': <Thermometer className="h-4 w-4 text-yellow-600" />,
      'onda_calor': <AlertTriangle className="h-4 w-4 text-red-600" />,
      'geada': <Package className="h-4 w-4 text-purple-600" />
    };
    return icons[tipo as keyof typeof icons] || <AlertTriangle className="h-4 w-4 text-gray-600" />;
  };

  return (
    <Card className="border-0 shadow-2xl bg-gradient-to-br from-white via-blue-50/30 to-purple-50/30">
      <CardHeader className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 text-white rounded-t-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <CardTitle className="text-2xl font-bold">{t('tokenization.create.title')}</CardTitle>
              <CardDescription className="text-blue-100">
                {t('tokenization.create.desc')}
              </CardDescription>
            </div>
          </div>
          <Badge className="bg-white/20 text-white border-white/30">
            ClimateWise Blockchain
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-8 space-y-8">
        {success && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-semibold text-green-800">{t('tokenization.create.success.title')}</p>
                <p className="text-sm text-green-600">{t('tokenization.create.success.desc')}</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">{t('tokenization.create.error.title')}</p>
                <p className="text-sm text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Event Information */}
          <div className="space-y-6">
            <div>
              <Label htmlFor="tipo" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                {getEventTypeIcon(formData.tipo)}
                {t('tokenization.create.eventInfo.title')}
              </Label>
              <Select value={formData.tipo || undefined} onValueChange={(value) => handleInputChange('tipo', value)}>
                <SelectTrigger className="border-gray-300">
                  <SelectValue placeholder={t('tokenization.create.eventInfo.placeholder')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enchente">🌊 {t('lp.events.floods')}</SelectItem>
                  <SelectItem value="seca">☀️ {t('lp.events.drought')}</SelectItem>
                  <SelectItem value="onda_calor">🔥 {t('demo.feature.tokenization.eventTypes.heatwave') || t('tokenization.eventTypes.heatwave')}</SelectItem>
                  <SelectItem value="geada">❄️ {t('lp.events.frost')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* ========== INTEGRATED LOCATION SELECTOR ========== */}
            <div className="p-5 bg-gradient-to-br from-emerald-50 to-cyan-50 rounded-xl border border-emerald-200 space-y-4">
              <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <MapPin className="h-4 w-4 text-emerald-600" />
                {t('tokenization.create.location.title')}
              </Label>

              {/* Current resolved location */}
              {locationName && (
                <div className="flex items-center gap-2 p-3 bg-white rounded-lg border border-emerald-200">
                  <MapPin className="h-4 w-4 text-emerald-500" />
                  <span className="font-medium text-emerald-800 text-sm">{locationName}</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    {formData.latitude && formData.longitude
                      ? `${parseFloat(formData.latitude).toFixed(4)}°, ${parseFloat(formData.longitude).toFixed(4)}°`
                      : ''}
                  </span>
                </div>
              )}

              {/* GPS Button */}
              <Button
                type="button"
                onClick={detectGPS}
                disabled={locLoading}
                variant="default"
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <Locate className="h-4 w-4 mr-2" />
                {locLoading ? t('tokenization.create.location.detecting') : t('tokenization.create.location.detect')}
              </Button>

              {/* City Search with Autocomplete */}
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2 relative">
                  <Input
                    placeholder="Buscar cidade..."
                    value={citySearch}
                    onChange={(e) => handleCityInput(e.target.value)}
                    onFocus={() => citySearch.length >= 2 && setShowSuggestions(citySuggestions.length > 0)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  />
                  {showSuggestions && citySuggestions.length > 0 && (
                    <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                      {citySuggestions.map((s, i) => (
                        <div
                          key={i}
                          className="px-3 py-2 hover:bg-emerald-50 cursor-pointer text-sm"
                          onClick={() => selectSuggestion(s)}
                        >
                          <span className="font-medium">{s.cidade}</span>
                          <span className="text-gray-500 ml-1">– {s.estado}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <Input
                  placeholder="UF"
                  value={stateSearch}
                  onChange={(e) => setStateSearch(e.target.value.toUpperCase())}
                  maxLength={2}
                  className="text-center uppercase"
                />
              </div>
              <Button type="button" onClick={searchByCity} variant="outline" className="w-full" disabled={locLoading}>
                <Search className="h-4 w-4 mr-2" /> {t('tokenization.create.location.searchCity')}
              </Button>

              {/* Recent Locations */}
              {recentLocations.length > 0 && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">{t('tokenization.create.location.recent')}</Label>
                  <div className="flex flex-wrap gap-1">
                    {recentLocations.slice(0, 3).map((loc, i) => (
                      <Button key={i} type="button" variant="ghost" size="sm" className="text-xs h-7 px-2" onClick={() => selectRecent(loc)}>
                        📍 {loc.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Advanced: Manual Coords Toggle */}
              <button
                type="button"
                onClick={() => setShowManualCoords(!showManualCoords)}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
              >
                {showManualCoords ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                {t('tokenization.create.location.manualCoords')}
              </button>

              {showManualCoords && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs text-gray-500">Latitude</Label>
                    <Input
                      type="number" step="0.000001" placeholder="-23.5505"
                      value={formData.latitude}
                      onChange={(e) => { handleInputChange('latitude', e.target.value); setLocationName(''); }}
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Longitude</Label>
                    <Input
                      type="number" step="0.000001" placeholder="-46.6333"
                      value={formData.longitude}
                      onChange={(e) => { handleInputChange('longitude', e.target.value); setLocationName(''); }}
                    />
                  </div>
                </div>
              )}

              {locError && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" /> {locError}
                </p>
              )}
            </div>
            {/* ========== END LOCATION SELECTOR ========== */}

            <div>
              <Label htmlFor="data_inicio" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <Calendar className="h-4 w-4 text-purple-600" />
                {t('tokenization.create.startDate')}
              </Label>
              <Input
                id="data_inicio"
                type="datetime-local"
                value={formData.data_inicio}
                onChange={(e) => handleInputChange('data_inicio', e.target.value)}
                className="border-gray-300"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="intensidade" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-orange-600" />
                  {t('tokenization.create.intensity')}
                </Label>
                <Input
                  id="intensidade"
                  type="number"
                  step="0.1"
                  placeholder="4.5"
                  value={formData.intensidade}
                  onChange={(e) => handleInputChange('intensidade', e.target.value)}
                  className="border-gray-300"
                />
              </div>

              <div>
                <Label htmlFor="probabilidade" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  {t('tokenization.create.probability')}
                </Label>
                <Input
                  id="probabilidade"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="85"
                  value={formData.probabilidade}
                  onChange={(e) => handleInputChange('probabilidade', e.target.value)}
                  className="border-gray-300"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="nivel_alerta" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                {t('tokenization.create.alertLevel.title')}
              </Label>
              <Select value={formData.nivel_alerta || undefined} onValueChange={(value) => handleInputChange('nivel_alerta', value)}>
                <SelectTrigger className="border-gray-300">
                  <SelectValue placeholder={t('tokenization.create.alertLevel.placeholder')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - {t('tokenization.create.alertLevel.low')}</SelectItem>
                  <SelectItem value="2">2 - {t('tokenization.create.alertLevel.moderate')}</SelectItem>
                  <SelectItem value="3">3 - {t('tokenization.create.alertLevel.high')}</SelectItem>
                  <SelectItem value="4">4 - {t('tokenization.create.alertLevel.veryHigh')}</SelectItem>
                  <SelectItem value="5">5 - {t('tokenization.create.alertLevel.extreme')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="descricao" className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2">
                <Package className="h-4 w-4 text-blue-600" />
                {t('tokenization.create.description.title')}
              </Label>
              <Textarea
                id="descricao"
                placeholder={t('tokenization.create.description.placeholder')}
                value={formData.descricao}
                onChange={(e) => handleInputChange('descricao', e.target.value)}
                className="border-gray-300 min-h-[100px]"
              />
            </div>
          </div>

          {/* Token Configuration */}
          <div className="space-y-6">
            <div className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border border-blue-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                {t('tokenization.create.config.title')}
              </h3>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="wallet_address" className="text-sm font-medium text-gray-700">
                    {t('tokenization.create.config.wallet')}
                  </Label>
                  <Input
                    id="wallet_address"
                    value={formData.wallet_address}
                    onChange={(e) => handleInputChange('wallet_address', e.target.value)}
                    className="border-gray-300 font-mono text-sm"
                  />
                </div>

                <div>
                  <Label htmlFor="token_supply" className="text-sm font-medium text-gray-700">
                    {t('tokenization.create.config.supply')}
                  </Label>
                  <Input
                    id="token_supply"
                    type="number"
                    value={formData.token_supply}
                    onChange={(e) => handleInputChange('token_supply', e.target.value)}
                    className="border-gray-300"
                  />
                </div>

                <div>
                  <Label htmlFor="decimals" className="text-sm font-medium text-gray-700">
                    {t('tokenization.create.config.decimals')}
                  </Label>
                  <Input
                    id="decimals"
                    type="number"
                    min="0"
                    max="18"
                    value={formData.decimals}
                    onChange={(e) => handleInputChange('decimals', e.target.value)}
                    className="border-gray-300"
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">{t('tokenization.create.preview.title')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">{t('tokenization.create.preview.symbol')}:</span>
                  <span className="font-medium">
                    {formData.tipo
                      ? formData.tipo.slice(0, 3).toUpperCase() + (formData.nivel_alerta || '0') + '25'
                      : '---'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">{t('tokenization.create.preview.supply')}:</span>
                  <span className="font-medium">{formData.token_supply.toLocaleString(language)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">{t('tokenization.create.preview.location')}:</span>
                  <span className="font-medium text-sm">
                    {locationName
                      ? <span className="text-emerald-700">📍 {locationName}</span>
                      : formData.latitude && formData.longitude
                        ? `${parseFloat(formData.latitude).toFixed(4)}°, ${parseFloat(formData.longitude).toFixed(4)}°`
                        : <span className="text-gray-400 italic">{t('tokenization.create.preview.selectAbove')}</span>
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">{t('tokenization.create.preview.date')}:</span>
                  <span className="font-medium text-sm">
                    {formData.data_inicio
                      ? new Date(formData.data_inicio).toLocaleString(language, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
                      : '---'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">{t('tokenization.create.preview.severity')}:</span>
                  <Badge variant="outline" className={
                    formData.nivel_alerta === '5' ? 'border-red-500 text-red-700' :
                      formData.nivel_alerta === '4' ? 'border-orange-500 text-orange-700' :
                        formData.nivel_alerta === '3' ? 'border-yellow-500 text-yellow-700' :
                          'border-gray-500 text-gray-700'
                  }>
                    {t('tokenization.eventTypes.severity')} {formData.nivel_alerta || '?'}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200">
          <Badge className="bg-blue-100 text-blue-800 border-blue-300">{t('tokenization.create.badges.temperature')}</Badge>
          <Badge className="bg-green-100 text-green-800 border-green-300">{t('tokenization.create.badges.precipitation')}</Badge>
          <Badge className="bg-purple-100 text-purple-800 border-purple-300">{t('tokenization.create.badges.wind')}</Badge>
          <Badge className="bg-orange-100 text-orange-800 border-orange-300">{t('tokenization.create.badges.waterLevel')}</Badge>
          <Badge className="bg-red-100 text-red-800 border-red-300">{t('tokenization.create.badges.extreme')}</Badge>
        </div>

        <Button
          onClick={handleCreateToken}
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 hover:from-blue-700 hover:via-purple-700 hover:to-blue-800 text-white py-4 text-lg font-semibold shadow-xl"
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 mr-3 animate-spin" />
              {t('tokenization.create.button.minting')}
            </>
          ) : (
            <>
              <Zap className="h-5 w-5 mr-3" />
              {t('tokenization.create.button.mint')}
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
