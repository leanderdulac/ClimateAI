import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MapPin, Locate, Clock, Search } from 'lucide-react';
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
  const [location, setLocation] = useState<LocalizacaoData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState<string>('');
  const [state, setState] = useState<string>('');
  const [cep, setCep] = useState<string>('');
  const [recentLocations, setRecentLocations] = useState<SavedLocation[]>([]);

  const { setSelectedLocation, setIsLoadingLocation } = useLocation();

  useEffect(() => {
    setRecentLocations(getRecentLocations());
  }, []);

  const handleLocationData = async (lat: number, lon: number, locationName?: string) => {
    if (!isWithinBrazil(lat, lon)) {
      setError('As coordenadas fornecidas estão fora do território brasileiro');
      setLoading(false);
      return;
    }

    try {
      setIsLoadingLocation(true);
      const locationData = await embrapaApi.getLocalizacao(lat, lon);
      setLocation(locationData);
      setSelectedLocation(locationData); // Atualizar contexto global

      if (locationData.cidade) {
        setCity(locationData.cidade);
      }
      if (locationData.estado) {
        setState(locationData.estado);
      }
      onLocationSelected?.(locationData);

      // Salvar nas localizações recentes
      saveRecentLocation({
        latitude: lat,
        longitude: lon,
        name: locationName || locationData.cidade || formatCoordinates(lat, lon),
        state: locationData.estado,
        timestamp: Date.now()
      });
      setRecentLocations(getRecentLocations());
    } catch (err) {
      console.error('Erro ao obter dados da localização:', err);
      setError('Não foi possível obter os dados desta localização');
    } finally {
      setLoading(false);
      setIsLoadingLocation(false);
    }
  };

  const detectLocation = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('Geolocalização não é suportada pelo seu navegador');
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
        setError(`Não foi possível obter sua localização: ${err.message}`);
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
      setError('Por favor, informe cidade e estado');
      return;
    }

    // Validar se o estado é válido
    const estadoValido = ESTADOS_BRASILEIROS.find(est => est.uf === state.toUpperCase());
    if (!estadoValido) {
      setError(`Estado "${state}" não é válido. Use uma UF válida (ex: SP, RJ, MG)`);
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
      setError(`Cidade "${city}" não encontrada no estado ${estadoValido.nome} (${state.toUpperCase()}). Verifique o nome da cidade e estado.`);
      setLoading(false);
    }
  };

  const searchLocationByCEP = async () => {
    const sanitizedCep = cep.replace(/\D/g, '');
    if (!sanitizedCep || !/^\d{8}$/.test(sanitizedCep)) {
      setError('Por favor, insira um CEP válido');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const locationData = await embrapaApi.getLocalizacaoPorCep(sanitizedCep);
      if (!locationData.latitude || !locationData.longitude) {
        setError('CEP não encontrado');
        setLoading(false);
        return;
      }

      if (locationData.cidade) {
        setCity(locationData.cidade);
      }
      if (locationData.estado) {
        setState(locationData.estado);
      }
      if (locationData.cep) {
        setCep(locationData.cep);
      }

      await handleLocationData(
        locationData.latitude,
        locationData.longitude,
        locationData.formattedAddress || `${locationData.cidade}, ${locationData.estado}`
      );
    } catch (err) {
      console.error('Erro ao buscar CEP:', err);
      setError('Falha ao buscar CEP. Por favor, tente novamente.');
      setLoading(false);
    }
  };

  const handleManualLocation = async () => {
    const latInput = document.getElementById('manual-lat') as HTMLInputElement;
    const lngInput = document.getElementById('manual-lng') as HTMLInputElement;

    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);

    if (isNaN(lat) || isNaN(lng)) {
      setError('Por favor, insira coordenadas válidas');
      return;
    }

    setLoading(true);
    setError(null);
    await handleLocationData(lat, lng);
  };

  const useRecentLocation = (recentLocation: SavedLocation) => {
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
          Localização
        </CardTitle>
        <CardDescription>
          Selecione sua localização para obter dados climáticos precisos
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Local atual */}
          <div className="space-y-2 bg-neutral-50 p-4 rounded-lg border border-neutral-200">
            {location ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Localização Atual</h3>
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
                  {loading ? "Detectando..." : "Detectar Minha Localização"}
                </Button>
              </div>
            )}
          </div>

          {/* Abas de busca */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              {/* Busca por cidade */}
              <div className="space-y-2">
                <Label>Cidade</Label>
                <Input
                  placeholder="Nome da cidade"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>UF</Label>
                <Input
                  placeholder="UF"
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
              Buscar por Cidade
            </Button>

            {/* Busca por CEP */}
            <div className="space-y-2">
              <Label>CEP</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="00000-000"
                  value={cep}
                  onChange={(e) => setCep(e.target.value)}
                  maxLength={9}
                />
                <Button
                  onClick={searchLocationByCEP}
                  variant="outline"
                  disabled={loading}
                >
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Coordenadas manuais */}
            <div className="space-y-2 pt-2 border-t border-neutral-200">
              <Label>Coordenadas Precisas</Label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-xs text-neutral-500">Latitude</Label>
                  <Input
                    id="manual-lat"
                    placeholder="-23.5505"
                    type="number"
                    step="0.000001"
                  />
                </div>
                <div>
                  <Label className="text-xs text-neutral-500">Longitude</Label>
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
                Usar Coordenadas
              </Button>
            </div>
          </div>

          {/* Localizações recentes */}
          {recentLocations.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-neutral-200">
              <Label className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Localizações Recentes
              </Label>
              <div className="space-y-1">
                {recentLocations.map((loc, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start text-left h-auto py-2"
                    onClick={() => useRecentLocation(loc)}
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
