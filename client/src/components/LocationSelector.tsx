import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MapPin, Locate, Clock, Search } from 'lucide-react';
import { useTranslation } from '@/hooks/useTranslation';
import { embrapaApi } from '@/lib/api';
import type { LocalizacaoData } from '@/lib/api';
import { useLocation } from '@/lib/LocationContext';
import {
  isWithinBrazil,
  formatCoordinates,
  saveRecentLocation,
  getRecentLocations,
  type SavedLocation
} from '@/lib/geoUtils';

// Lista de estados brasileiros válidos
const ESTADOS_BRASILEIROS = [
  { uf: 'AC', nome: 'Acre' },
  { uf: 'AL', nome: 'Alagoas' },
  { uf: 'AP', nome: 'Amapá' },
  { uf: 'AM', nome: 'Amazonas' },
  { uf: 'BA', nome: 'Bahia' },
  { uf: 'CE', nome: 'Ceará' },
  { uf: 'DF', nome: 'Distrito Federal' },
  { uf: 'ES', nome: 'Espírito Santo' },
  { uf: 'GO', nome: 'Goiás' },
  { uf: 'MA', nome: 'Maranhão' },
  { uf: 'MT', nome: 'Mato Grosso' },
  { uf: 'MS', nome: 'Mato Grosso do Sul' },
  { uf: 'MG', nome: 'Minas Gerais' },
  { uf: 'PA', nome: 'Pará' },
  { uf: 'PB', nome: 'Paraíba' },
  { uf: 'PR', nome: 'Paraná' },
  { uf: 'PE', nome: 'Pernambuco' },
  { uf: 'PI', nome: 'Piauí' },
  { uf: 'RJ', nome: 'Rio de Janeiro' },
  { uf: 'RN', nome: 'Rio Grande do Norte' },
  { uf: 'RS', nome: 'Rio Grande do Sul' },
  { uf: 'RO', nome: 'Rondônia' },
  { uf: 'RR', nome: 'Roraima' },
  { uf: 'SC', nome: 'Santa Catarina' },
  { uf: 'SP', nome: 'São Paulo' },
  { uf: 'SE', nome: 'Sergipe' },
  { uf: 'TO', nome: 'Tocantins' }
];

interface LocationSelectorProps {
  onLocationSelected?: (location: LocalizacaoData) => void;
}

export function LocationSelector({ onLocationSelected }: LocationSelectorProps) {
  const { t } = useTranslation();
  const [location, setLocation] = useState<LocalizacaoData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState<string>('');
  const [state, setState] = useState<string>('');
  const [recentLocations, setRecentLocations] = useState<SavedLocation[]>([]);
  const [citySuggestions, setCitySuggestions] = useState<LocalizacaoData[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);

  const { setSelectedLocation, setIsLoadingLocation } = useLocation();

  useEffect(() => {
    setRecentLocations(getRecentLocations());
  }, []);

  // Buscar sugestões de cidades
  const searchCitySuggestions = async (term: string) => {
    if (term.length < 2) {
      setCitySuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const suggestions = await embrapaApi.buscarCidades(term);
      setCitySuggestions(suggestions);
      setShowSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Erro ao buscar sugestões de cidades:', error);
      setCitySuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Handler para mudança no campo cidade
  const handleCityChange = (value: string) => {
    setCity(value);
    searchCitySuggestions(value);
  };

  // Selecionar uma sugestão
  const selectCitySuggestion = async (suggestion: LocalizacaoData) => {
    setCity(suggestion.cidade || '');
    setState(suggestion.estado || '');
    setCitySuggestions([]);
    setShowSuggestions(false);

    // Buscar automaticamente a localização completa
    setLoading(true);
    setError(null);

    try {
      await handleLocationData(
        suggestion.latitude,
        suggestion.longitude,
        `${suggestion.cidade}, ${suggestion.estado}`
      );
    } catch (err) {
      console.error('Erro ao selecionar cidade:', err);
      setError(t('location.errors.cityLoad'));
      setLoading(false);
    }
  };

  const handleLocationData = async (lat: number, lon: number, locationName?: string) => {
    if (!isWithinBrazil(lat, lon)) {
      setError(t('location.errors.outside'));
      setLoading(false);
      return;
    }

    try {
      setIsLoadingLocation(true);
      const locationData = await embrapaApi.getLocalizacao(lat, lon);

      // Combine API data with any provided location name from suggestions
      const combinedLocationData = {
        ...locationData,
        cidade: locationData.cidade || (locationName ? locationName.split(',')[0].trim() : undefined),
        estado: locationData.estado || (locationName && locationName.includes(',') ?
          locationName.split(',')[1].split('-')[0].trim() : undefined)
      };

      setLocation(combinedLocationData);
      setSelectedLocation(combinedLocationData); // Atualizar contexto global

      if (combinedLocationData.cidade) {
        setCity(combinedLocationData.cidade);
      }
      if (combinedLocationData.estado) {
        setState(combinedLocationData.estado);
      }
      onLocationSelected?.(combinedLocationData);

      // Salvar nas localizações recentes
      saveRecentLocation({
        latitude: lat,
        longitude: lon,
        name: locationName || combinedLocationData.cidade || formatCoordinates(lat, lon),
        state: combinedLocationData.estado,
        timestamp: Date.now()
      });
      setRecentLocations(getRecentLocations());
    } catch (err) {
      console.error('Erro ao obter dados da localização:', err);
      setError(t('location.errors.notFound'));
    } finally {
      setLoading(false);
      setIsLoadingLocation(false);
    }
  };

  const detectLocation = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError(t('location.errors.geolocation'));
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        await handleLocationData(latitude, longitude);
      },

      (err) => {
        console.error('Erro de geolocalização:', err);
        setError(`${t('location.errors.geoFail')}: ${err.message}`);
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      }
    );
  };

  const searchLocationByCity = async () => {
    if (!city || !state) {
      setError(t('location.errors.cityState'));
      return;
    }

    // Validar se o estado é válido
    const estadoValido = ESTADOS_BRASILEIROS.find(est => est.uf === state.toUpperCase());
    if (!estadoValido) {
      setError(`Estado "${state}" ${t('location.errors.invalidState')}`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const locationData = await embrapaApi.getLocalizacaoPorCidade(city, state);
      if (locationData.cidade) {
        setCity(locationData.cidade);
      }
      if (locationData.estado) {
        setState(locationData.estado);
      }
      await handleLocationData(
        locationData.latitude,
        locationData.longitude,
        locationData.formattedAddress || `${locationData.cidade}, ${locationData.estado}`
      );
    } catch (err) {
      console.error('Erro ao buscar coordenadas:', err);
      setError(`Cidade "${city}" ${t('location.errors.cityNotFound')} ${estadoValido.nome} (${state.toUpperCase()}). ${t('location.errors.cityNotFoundDetails')}`);
      setLoading(false);
    }
  };

  const handleManualLocation = async () => {
    const latInput = document.getElementById('manual-lat') as HTMLInputElement;
    const lngInput = document.getElementById('manual-lng') as HTMLInputElement;

    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);

    if (isNaN(lat) || isNaN(lng)) {
      setError(t('location.errors.invalidCoords'));
      return;
    }

    setLoading(true);
    setError(null);
    await handleLocationData(lat, lng);
  };

  const handleSelectRecentLocation = (recentLocation: SavedLocation) => {
    setLoading(true);
    setError(null);
    handleLocationData(
      recentLocation.latitude,
      recentLocation.longitude,
      recentLocation.name
    );
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5" />
          {t('location.title')}
        </CardTitle>
        <CardDescription>
          {t('location.subtitle')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Local atual */}
          <div className="space-y-2 bg-neutral-50 p-4 rounded-lg border border-neutral-200">
            {location ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{t('location.current')}</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={detectLocation}
                    disabled={loading}
                  >
                    <Locate className="h-4 w-4" />
                  </Button>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-neutral-700">
                    {formatCoordinates(location.latitude, location.longitude)}
                  </p>
                  {location.cidade && (
                    <p className="text-sm font-medium text-neutral-700">
                      {location.cidade}, {location.estado}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <Button
                  onClick={detectLocation}
                  disabled={loading}
                  variant="default"
                  size="lg"
                >
                  <Locate className="h-5 w-5 mr-2" />
                  {loading ? t('location.detecting') : t('location.detect')}
                </Button>
              </div>
            )}
          </div>

          {/* Abas de busca */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {/* Busca por cidade */}
              <div className="space-y-2 relative">
                <Label>{t('location.city')}</Label>
                <Input
                  placeholder={t('location.cityPlaceholder')}
                  value={city}
                  onChange={(e) => handleCityChange(e.target.value)}
                  onFocus={() => city.length >= 2 && setShowSuggestions(citySuggestions.length > 0)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)} // Delay para permitir clique
                />
                {showSuggestions && citySuggestions.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {citySuggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                        onClick={() => selectCitySuggestion(suggestion)}
                      >
                        <div className="font-medium">{suggestion.cidade}</div>
                        <div className="text-gray-500 text-xs">{suggestion.estado} - {suggestion.estado}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t('location.state')}</Label>
                <Input
                  placeholder={t('location.state')}
                  value={state}
                  onChange={(e) => setState(e.target.value.toUpperCase())}
                  maxLength={2}
                  className="text-center uppercase"
                />
              </div>
            </div>
            <Button
              onClick={searchLocationByCity}
              className="w-full"
              variant="outline"
              disabled={loading}
            >
              <Search className="h-4 w-4 mr-2" />
              {t('location.searchByCity')}
            </Button>

            {/* Coordenadas manuais */}
            <div className="space-y-2 pt-2 border-t border-neutral-200">
              <Label>{t('location.coordinates')}</Label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-xs text-neutral-500">{t('location.latitude')}</Label>
                  <Input
                    id="manual-lat"
                    placeholder="-23.5505"
                    type="number"
                    step="0.000001"
                  />
                </div>
                <div>
                  <Label className="text-xs text-neutral-500">{t('location.longitude')}</Label>
                  <Input
                    id="manual-lng"
                    placeholder="-46.6333"
                    type="number"
                    step="0.000001"
                  />
                </div>
              </div>
              <Button
                onClick={handleManualLocation}
                className="w-full"
                variant="outline"
                disabled={loading}
              >
                <MapPin className="h-4 w-4 mr-2" />
                {t('location.useCoordinates')}
              </Button>
            </div>
          </div>

          {/* Localizações recentes */}
          {recentLocations.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-neutral-200">
              <Label className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {t('location.recent')}
              </Label>
              <div className="space-y-1">
                {recentLocations.map((loc, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start text-left h-auto py-2"
                    onClick={() => handleSelectRecentLocation(loc)}
                  >
                    <div className="flex flex-col items-start">
                      <span className="text-sm font-medium">{loc.name}</span>
                      <span className="text-xs text-neutral-500">
                        {formatCoordinates(loc.latitude, loc.longitude)}
                      </span>
                    </div>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 flex items-center gap-2">
              <div className="rounded-full bg-red-100 p-1">
                <MapPin className="h-4 w-4" />
              </div>
              {error}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
