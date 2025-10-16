// Real API service for backend integration
import axios from 'axios';

// Nominatim API base URL for real geocoding
const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org';

export interface ClimateData {
  date: string;
  temperature: number;
  temperature_max?: number;
  temperature_min?: number;
  temperature_apparent?: number;
  precipitation: number;
  precipitation_probability?: number;
  humidity: number;
  windSpeed?: number;
  wind_speed?: number;
  windDirection?: number;
  pressure?: number;
  weather_code?: number;
  weatherCode?: number;
}

export interface LocationData {
  latitude: number;
  longitude: number;
  city?: string;
  state?: string;
  stateName?: string;
  country?: string;
  postcode?: string;
  formattedAddress?: string;
  distanceKm?: number;
  bairro?: string;
  neighborhood?: string;
  logradouro?: string;
  street?: string;
  complemento?: string;
  cep?: string;
}

export interface ForecastData {
  date?: string;
  data?: string;
  temperature: number;
  temperatura_max?: number;
  precipitation: number;
  precipitacao?: number;
  humidity: number;
  windSpeed: number;
  vento_velocidade?: number;
  cloudCover: number;
}

export interface RiskAnalysis {
  riskLevel: number;
  riskFactors: string[];
  recommendations: string[];
}

const baseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  'http://localhost:8000/api/v1';

// Mock data para fallback quando API não disponível
const mockClimateData = (days: number = 30): ClimateData[] => {
  const data: ClimateData[] = [];
  const hoje = new Date();
  for (let i = 0; i < days; i++) {
    const date = new Date(hoje);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toISOString().split('T')[0],
      temperature: 20 + Math.random() * 10,
      temperature_max: 25 + Math.random() * 8,
      temperature_min: 15 + Math.random() * 5,
      precipitation: Math.random() * 20,
      humidity: 60 + Math.random() * 30,
      windSpeed: 5 + Math.random() * 15,
      pressure: 1010 + Math.random() * 20,
      weather_code: Math.floor(Math.random() * 10)
    });
  }
  return data;
};

const mockForecastData = (days: number = 7): ForecastData[] => {
  const data: ForecastData[] = [];
  const hoje = new Date();
  for (let i = 0; i < days; i++) {
    const date = new Date(hoje);
    date.setDate(date.getDate() + i);
    data.push({
      date: date.toISOString().split('T')[0],
      temperature: 20 + Math.random() * 10,
      precipitation: Math.random() * 20,
      humidity: 60 + Math.random() * 30,
      windSpeed: 5 + Math.random() * 15,
      cloudCover: Math.random() * 100
    });
  }
  return data;
};

const mockLocationData = (lat: number, lon: number): LocationData => ({
  latitude: lat,
  longitude: lon,
  city: 'Cidade de Exemplo',
  state: 'SP',
  stateName: 'São Paulo',
  country: 'Brasil',
  formattedAddress: `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`
});

class EmbrapaApiService {
  private isApiAvailable = true;
  private useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true' ||
                        !import.meta.env.VITE_API_BASE_URL ||
                        import.meta.env.VITE_API_BASE_URL === '';

  // Real geocoding using Nominatim API
  private async nominatimSearch(query: string, limit: number = 10): Promise<any[]> {
    try {
      const response = await axios.get(`${NOMINATIM_BASE_URL}/search`, {
        params: {
          q: query,
          format: 'json',
          addressdetails: 1,
          limit: limit,
          countrycodes: 'br', // Limit to Brazil
          'accept-language': 'pt-BR,en'
        },
        timeout: 5000,
        headers: {
          'User-Agent': 'ClimateAI/1.0'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Erro na busca Nominatim:', error);
      throw error;
    }
  }

  // Real reverse geocoding using Nominatim API
  private async nominatimReverse(lat: number, lon: number): Promise<any> {
    try {
      const response = await axios.get(`${NOMINATIM_BASE_URL}/reverse`, {
        params: {
          lat: lat,
          lon: lon,
          format: 'json',
          addressdetails: 1,
          'accept-language': 'pt-BR,en'
        },
        timeout: 5000,
        headers: {
          'User-Agent': 'ClimateAI/1.0'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Erro no reverse geocoding Nominatim:', error);
      throw error;
    }
  }

  private async apiGet<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    try {
      const response = await axios.get(`${baseUrl}${endpoint}`, { params, timeout: 5000 });
      this.isApiAvailable = true;
      return response.data;
    } catch (error) {
      console.warn('API não disponível, usando dados mock:', error instanceof Error ? error.message : 'Unknown error');
      this.isApiAvailable = false;
      throw error;
    }
  }

  private async apiPost<T>(endpoint: string, data?: any): Promise<T> {
    try {
      const response = await axios.post(`${baseUrl}${endpoint}`, data, { timeout: 5000 });
      this.isApiAvailable = true;
      return response.data;
    } catch (error) {
      console.warn('API não disponível, usando dados mock:', error instanceof Error ? error.message : 'Unknown error');
      this.isApiAvailable = false;
      throw error;
    }
  }

  async getClimateData(latitude: number, longitude: number, startDate: string, endDate: string): Promise<ClimateData[]> {
    if (this.useMockData) {
      // Usar dados mock apenas quando explicitamente configurado
      console.log('🌤️ Usando dados climáticos mock (configurado)');
      const days = Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24));
      return mockClimateData(Math.min(days, 365));
    }

    try {
      // Tentar API real primeiro
      return await this.apiGet('/clima/historico', {
        latitude,
        longitude,
        data_inicio: startDate,
        data_fim: endDate
      });
    } catch (error) {
      console.error('❌ API climática real falhou:', error);
      // Em produção, sem mock configurado, devemos falhar graciosamente
      // mas por enquanto, usar mock como último recurso
      console.warn('⚠️ Fallback para dados climáticos mock (emergência)');
      const days = Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24));
      return mockClimateData(Math.min(days, 365));
    }
  }

  async getCurrentClimate(latitude: number, longitude: number): Promise<ClimateData> {
    if (this.useMockData) {
      // Usar dados mock apenas quando explicitamente configurado
      console.log('🌤️ Usando clima atual mock (configurado)');
      return mockClimateData(1)[0];
    }

    try {
      // Tentar API real primeiro
      return await this.apiGet('/clima/atual', {
        latitude,
        longitude
      });
    } catch (error) {
      console.error('❌ API clima atual real falhou:', error);
      // Em produção, sem mock configurado, devemos falhar graciosamente
      console.warn('⚠️ Fallback para clima atual mock (emergência)');
      return mockClimateData(1)[0];
    }
  }

  async getLocationData(latitude: number, longitude: number): Promise<LocationData> {
    try {
      const location = await this.apiGet('/localizacao/coordenadas', {
        latitude,
        longitude
      });
      return this.normalizeLocation(location, { latitude, longitude });
    } catch (error) {
      // Fallback para dados mock
      console.log('Usando localização mock');
      return mockLocationData(latitude, longitude);
    }
  }

  async getLocationByCep(cep: string): Promise<LocationData> {
    try {
      const sanitized = cep.replace(/\D/g, '');
      console.log(`🔍 [API] Buscando CEP via API: ${sanitized}`);
      const location = await this.apiGet(`/localizacao/cep/${sanitized}`);
      console.log('✅ [API] CEP encontrado via API');
      return this.normalizeLocation(location);
    } catch (error) {
      // Fallback para dados mock
      console.warn(`⚠️ [API] CEP não encontrado, usando mock (São Paulo)`);
      return mockLocationData(-23.5505, -46.6333);
    }
  }

  private getMockLocationData(city: string, state: string): LocationData {
    const cityMocks: { [key: string]: { lat: number; lon: number; state: string } } = {
      // Capitais estaduais
      'rio branco': { lat: -9.9747, lon: -67.8097, state: 'AC' },
      'maceió': { lat: -9.6498, lon: -35.7089, state: 'AL' },
      'maceio': { lat: -9.6498, lon: -35.7089, state: 'AL' },
      'manaus': { lat: -3.1190, lon: -60.0217, state: 'AM' },
      'salvador': { lat: -12.9714, lon: -38.5014, state: 'BA' },
      'fortaleza': { lat: -3.7319, lon: -38.5267, state: 'CE' },
      'brasília': { lat: -15.7942, lon: -47.8822, state: 'DF' },
      'brasilia': { lat: -15.7942, lon: -47.8822, state: 'DF' },
      'vitória': { lat: -20.3155, lon: -40.3436, state: 'ES' },
      'vitoria': { lat: -20.3155, lon: -40.3436, state: 'ES' },
      'goiânia': { lat: -15.7942, lon: -48.8694, state: 'GO' },
      'goiania': { lat: -15.7942, lon: -48.8694, state: 'GO' },
      'são luís': { lat: -2.5307, lon: -44.3068, state: 'MA' },
      'sao luis': { lat: -2.5307, lon: -44.3068, state: 'MA' },
      'cuiabá': { lat: -15.5989, lon: -56.0949, state: 'MT' },
      'cuiaba': { lat: -15.5989, lon: -56.0949, state: 'MT' },
      'campo grande': { lat: -20.4697, lon: -54.6201, state: 'MS' },
      'belo horizonte': { lat: -19.9167, lon: -43.9345, state: 'MG' },
      'belo': { lat: -19.9167, lon: -43.9345, state: 'MG' },
      'belém': { lat: -1.4558, lon: -48.5044, state: 'PA' },
      'belem': { lat: -1.4558, lon: -48.5044, state: 'PA' },
      'joão pessoa': { lat: -7.1195, lon: -34.8450, state: 'PB' },
      'joao pessoa': { lat: -7.1195, lon: -34.8450, state: 'PB' },
      'curitiba': { lat: -25.4284, lon: -49.2733, state: 'PR' },
      'recife': { lat: -8.0476, lon: -34.8770, state: 'PE' },
      'teresina': { lat: -5.0892, lon: -42.8034, state: 'PI' },
      'rio de janeiro': { lat: -22.9068, lon: -43.1729, state: 'RJ' },
      'rio_de_janeiro': { lat: -22.9068, lon: -43.1729, state: 'RJ' },
      'rio': { lat: -22.9068, lon: -43.1729, state: 'RJ' },
      'natal': { lat: -5.7945, lon: -35.2110, state: 'RN' },
      'porto alegre': { lat: -30.0346, lon: -51.2177, state: 'RS' },
      'porto_alegre': { lat: -30.0346, lon: -51.2177, state: 'RS' },
      'porto velho': { lat: -8.7612, lon: -63.9004, state: 'RO' },
      'boa vista': { lat: 2.8197, lon: -60.6714, state: 'RR' },
      'florianópolis': { lat: -27.5973, lon: -48.5500, state: 'SC' },
      'florianopolis': { lat: -27.5973, lon: -48.5500, state: 'SC' },
      'são paulo': { lat: -23.5505, lon: -46.6333, state: 'SP' },
      'sao paulo': { lat: -23.5505, lon: -46.6333, state: 'SP' },
      'sp': { lat: -23.5505, lon: -46.6333, state: 'SP' },
      'aracaju': { lat: -10.9472, lon: -37.0731, state: 'SE' },
      'palmas': { lat: -10.2491, lon: -48.3243, state: 'TO' },
      // Cidades importantes adicionais
      'campinas': { lat: -22.9099, lon: -47.0626, state: 'SP' },
      'santos': { lat: -23.9608, lon: -46.3336, state: 'SP' },
      'ribeirão preto': { lat: -21.1783, lon: -47.8065, state: 'SP' },
      'ribeirao preto': { lat: -21.1783, lon: -47.8065, state: 'SP' },
      'sorocaba': { lat: -23.5015, lon: -47.4581, state: 'SP' },
      'niterói': { lat: -22.8832, lon: -43.1034, state: 'RJ' },
      'niteroi': { lat: -22.8832, lon: -43.1034, state: 'RJ' },
      'duque de caxias': { lat: -22.7858, lon: -43.3049, state: 'RJ' },
      'contagem': { lat: -19.9386, lon: -44.0539, state: 'MG' },
      'uberlândia': { lat: -18.9186, lon: -48.2772, state: 'MG' },
      'uberlandia': { lat: -18.9186, lon: -48.2772, state: 'MG' },
      'juiz de fora': { lat: -21.7642, lon: -43.3503, state: 'MG' },
      'londrina': { lat: -23.3045, lon: -51.1696, state: 'PR' },
      'maringá': { lat: -23.4253, lon: -51.9382, state: 'PR' },
      'maringa': { lat: -23.4253, lon: -51.9382, state: 'PR' },
      'joinville': { lat: -26.3044, lon: -48.8464, state: 'SC' },
      'blumenau': { lat: -26.9194, lon: -49.0661, state: 'SC' },
      'caxias do sul': { lat: -29.1685, lon: -51.1794, state: 'RS' },
      'pelotas': { lat: -31.7714, lon: -52.3425, state: 'RS' },
      'anápolis': { lat: -16.3285, lon: -48.9534, state: 'GO' },
      'anapolis': { lat: -16.3285, lon: -48.9534, state: 'GO' },
      'aparecida de goiânia': { lat: -16.8198, lon: -49.2469, state: 'GO' },
      'vila velha': { lat: -20.3297, lon: -40.3074, state: 'ES' },
      'serra': { lat: -20.1286, lon: -40.3074, state: 'ES' }
    };

    const key = city.toLowerCase().trim();
    const mockData = cityMocks[key];

    if (mockData) {
      console.log(`✅ [MOCK] Mock encontrado para: ${city}`);
      return {
        ...mockLocationData(mockData.lat, mockData.lon),
        city,
        state: state.toUpperCase()
      };
    }

    console.warn(`⚠️ [MOCK] Cidade não encontrada em mock, usando padrão (São Paulo)`);
    return { ...mockLocationData(-23.5505, -46.6333), city, state: state.toUpperCase() };
  }

  private getMockCitySearch(term: string, state?: string): LocationData[] {
    const estadosMap: { [key: string]: string } = {
      'SP': 'São Paulo',
      'RJ': 'Rio de Janeiro',
      'MG': 'Minas Gerais',
      'DF': 'Distrito Federal',
      'PR': 'Paraná',
      'BA': 'Bahia',
      'SC': 'Santa Catarina',
      'RS': 'Rio Grande do Sul',
      'GO': 'Goiás',
      'ES': 'Espírito Santo',
      'AC': 'Acre',
      'AL': 'Alagoas',
      'AM': 'Amazonas',
      'CE': 'Ceará',
      'MA': 'Maranhão',
      'MT': 'Mato Grosso',
      'MS': 'Mato Grosso do Sul',
      'PA': 'Pará',
      'PB': 'Paraíba',
      'PE': 'Pernambuco',
      'PI': 'Piauí',
      'RN': 'Rio Grande do Norte',
      'RO': 'Rondônia',
      'RR': 'Roraima',
      'SE': 'Sergipe',
      'TO': 'Tocantins'
    };

    const mockCities = [
      // Capitais estaduais
      { city: 'Rio Branco', state: 'AC', latitude: -9.9747, longitude: -67.8097 },
      { city: 'Maceió', state: 'AL', latitude: -9.6498, longitude: -35.7089 },
      { city: 'Manaus', state: 'AM', latitude: -3.1190, longitude: -60.0217 },
      { city: 'Salvador', state: 'BA', latitude: -12.9714, longitude: -38.5014 },
      { city: 'Fortaleza', state: 'CE', latitude: -3.7319, longitude: -38.5267 },
      { city: 'Brasília', state: 'DF', latitude: -15.7942, longitude: -47.8822 },
      { city: 'Vitória', state: 'ES', latitude: -20.3155, longitude: -40.3436 },
      { city: 'Goiânia', state: 'GO', latitude: -15.7942, longitude: -48.8694 },
      { city: 'São Luís', state: 'MA', latitude: -2.5307, longitude: -44.3068 },
      { city: 'Cuiabá', state: 'MT', latitude: -15.5989, longitude: -56.0949 },
      { city: 'Campo Grande', state: 'MS', latitude: -20.4697, longitude: -54.6201 },
      { city: 'Belo Horizonte', state: 'MG', latitude: -19.9167, longitude: -43.9345 },
      { city: 'Belém', state: 'PA', latitude: -1.4558, longitude: -48.5044 },
      { city: 'João Pessoa', state: 'PB', latitude: -7.1195, longitude: -34.8450 },
      { city: 'Curitiba', state: 'PR', latitude: -25.4284, longitude: -49.2733 },
      { city: 'Recife', state: 'PE', latitude: -8.0476, longitude: -34.8770 },
      { city: 'Teresina', state: 'PI', latitude: -5.0892, longitude: -42.8034 },
      { city: 'Rio de Janeiro', state: 'RJ', latitude: -22.9068, longitude: -43.1729 },
      { city: 'Natal', state: 'RN', latitude: -5.7945, longitude: -35.2110 },
      { city: 'Porto Alegre', state: 'RS', latitude: -30.0346, longitude: -51.2177 },
      { city: 'Porto Velho', state: 'RO', latitude: -8.7612, longitude: -63.9004 },
      { city: 'Boa Vista', state: 'RR', latitude: 2.8197, longitude: -60.6714 },
      { city: 'Florianópolis', state: 'SC', latitude: -27.5973, longitude: -48.5500 },
      { city: 'São Paulo', state: 'SP', latitude: -23.5505, longitude: -46.6333 },
      { city: 'Aracaju', state: 'SE', latitude: -10.9472, longitude: -37.0731 },
      { city: 'Palmas', state: 'TO', latitude: -10.2491, longitude: -48.3243 },
      // Cidades importantes adicionais
      { city: 'Campinas', state: 'SP', latitude: -22.9099, longitude: -47.0626 },
      { city: 'Santos', state: 'SP', latitude: -23.9608, longitude: -46.3336 },
      { city: 'Ribeirão Preto', state: 'SP', latitude: -21.1783, longitude: -47.8065 },
      { city: 'Sorocaba', state: 'SP', latitude: -23.5015, longitude: -47.4581 },
      { city: 'Niterói', state: 'RJ', latitude: -22.8832, longitude: -43.1034 },
      { city: 'Duque de Caxias', state: 'RJ', latitude: -22.7858, longitude: -43.3049 },
      { city: 'Contagem', state: 'MG', latitude: -19.9386, longitude: -44.0539 },
      { city: 'Uberlândia', state: 'MG', latitude: -18.9186, longitude: -48.2772 },
      { city: 'Juiz de Fora', state: 'MG', latitude: -21.7642, longitude: -43.3503 },
      { city: 'Londrina', state: 'PR', latitude: -23.3045, longitude: -51.1696 },
      { city: 'Maringá', state: 'PR', latitude: -23.4253, longitude: -51.9382 },
      { city: 'Joinville', state: 'SC', latitude: -26.3044, longitude: -48.8464 },
      { city: 'Blumenau', state: 'SC', latitude: -26.9194, longitude: -49.0661 },
      { city: 'Caxias do Sul', state: 'RS', latitude: -29.1685, longitude: -51.1794 },
      { city: 'Pelotas', state: 'RS', latitude: -31.7714, longitude: -52.3425 },
      { city: 'Anápolis', state: 'GO', latitude: -16.3285, longitude: -48.9534 },
      { city: 'Aparecida de Goiânia', state: 'GO', latitude: -16.8198, longitude: -49.2469 },
      { city: 'Vila Velha', state: 'ES', latitude: -20.3297, longitude: -40.2925 },
      { city: 'Serra', state: 'ES', latitude: -20.1286, longitude: -40.3074 }
    ].filter(c =>
      c.city.toLowerCase().includes(term.toLowerCase()) ||
      (state && c.state === state.toUpperCase())
    );

    console.log(`✅ Cidades mock encontradas: ${mockCities.length} resultado(s)`);

    return mockCities.map(c => ({
      ...mockLocationData(c.latitude, c.longitude),
      city: c.city,
      state: c.state,
      stateName: estadosMap[c.state] || c.state
    }));
  }

  async getLocationByCity(city: string, state: string): Promise<LocationData> {
    if (this.useMockData) {
      // Usar dados mock diretamente
      console.log(`🔍 [MOCK] Buscando cidade mock: ${city}, ${state}`);
      return this.getMockLocationData(city, state);
    }

    try {
      // Busca real usando Nominatim
      console.log(`🔍 [NOMINATIM] Buscando cidade real: ${city}, ${state}`);
      const query = `${city}, ${state}, Brasil`;
      const results = await this.nominatimSearch(query, 1);

      if (results && results.length > 0) {
        const result = results[0];
        const address = result.address || {};

        console.log('✅ [NOMINATIM] Cidade encontrada via geocoding real');

        return {
          latitude: parseFloat(result.lat),
          longitude: parseFloat(result.lon),
          city: address.city || address.town || address.village || city,
          state: address.state || state,
          stateName: address.state || state,
          country: address.country || 'Brasil',
          formattedAddress: result.display_name,
          postcode: address.postcode
        };
      }

      throw new Error('Cidade não encontrada');
    } catch (error) {
      console.warn(`⚠️ [NOMINATIM] Geocoding falhou para: ${city}, ${state}`, error);
      // Fallback para dados mock se geocoding falhar
      console.log('🔄 Fallback para dados mock');
      return this.getMockLocationData(city, state);
    }
  }

  async searchCities(term: string, state?: string): Promise<LocationData[]> {
    if (this.useMockData) {
      // Fallback para dados mock de cidades
      console.log('🌍 Usando busca de cidades mock');
      return this.getMockCitySearch(term, state);
    }

    try {
      // Busca real usando Nominatim
      console.log(`🔍 [NOMINATIM] Buscando cidades reais: "${term}"${state ? `, ${state}` : ''}`);
      const query = state ? `${term}, ${state}, Brasil` : `${term}, Brasil`;
      const results = await this.nominatimSearch(query, 20);

      if (results && results.length > 0) {
        const cities: LocationData[] = results
          .filter((result: any) => {
            // Filtrar apenas cidades, vilas, towns
            const address = result.address || {};
            return address.city || address.town || address.village || address.municipality;
          })
          .map((result: any) => {
            const address = result.address || {};

            return {
              latitude: parseFloat(result.lat),
              longitude: parseFloat(result.lon),
              city: address.city || address.town || address.village || address.municipality,
              state: address.state,
              stateName: address.state,
              country: address.country || 'Brasil',
              formattedAddress: result.display_name,
              postcode: address.postcode
            };
          });

        console.log(`✅ [NOMINATIM] Encontradas ${cities.length} cidades reais`);
        return cities;
      }

      return [];
    } catch (error) {
      console.warn(`⚠️ [NOMINATIM] Busca falhou para: "${term}"`, error);
      // Fallback para dados mock se geocoding falhar
      console.log('🔄 Fallback para busca mock');
      return this.getMockCitySearch(term, state);
    }
  }

  async getWeatherForecast(latitude: number, longitude: number, days: number = 7): Promise<ForecastData[]> {
    if (this.useMockData) {
      // Usar dados mock apenas quando explicitamente configurado
      console.log('🌤️ Usando previsão mock (configurado)');
      return mockForecastData(Math.min(days, 30));
    }

    try {
      const response = await this.apiGet('/clima/previsao', {
        latitude,
        longitude,
        dias: days
      }) as any;

      // O backend retorna { previsao: [...], ... }, então extraímos o array
      const forecastArray = response.previsao || response;
      return Array.isArray(forecastArray) ? forecastArray : [];
    } catch (error) {
      console.error('❌ API previsão real falhou:', error);
      // Em produção, sem mock configurado, devemos falhar graciosamente
      console.warn('⚠️ Fallback para previsão mock (emergência)');
      return mockForecastData(Math.min(days, 30));
    }
  }

  async getAgriculturalZoning(latitude: number, longitude: number, crop: string): Promise<any> {
    return this.apiGet('/clima/zarc', {
      latitude,
      longitude,
      cultura: crop
    });
  }

  async getRiskAnalysis(latitude: number, longitude: number, startDate?: string, endDate?: string): Promise<RiskAnalysis> {
    return this.apiGet('/clima/risco', {
      latitude,
      longitude,
      data_inicio: startDate,
      data_fim: endDate
    });
  }

  async getHistoricalRiskIndex(latitude: number, longitude: number, years: number = 10): Promise<number> {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - years);

    const riskAnalysis = await this.getRiskAnalysis(
      latitude,
      longitude,
      startDate.toISOString().split('T')[0],
      endDate.toISOString().split('T')[0]
    );

    return riskAnalysis.riskLevel;
  }

  async calculateAdvancedPremium(data: {
    latitude: number;
    longitude: number;
    frequency: number;
    severity: number;
    asset_value: number;
    confidence_level: number;
  }): Promise<any> {
    return this.apiPost('/clima/calculo-avancado-premio', data);
  }

  private normalizeLocation(data: any, fallback?: { latitude: number; longitude: number }): LocationData {
    if (!data && fallback) {
      return {
        latitude: fallback.latitude,
        longitude: fallback.longitude
      };
    }

    const latitude = data?.latitude ?? fallback?.latitude;
    const longitude = data?.longitude ?? fallback?.longitude;

    return {
      latitude,
      longitude,
      city: data?.city ?? data?.cidade,
      state: data?.state ?? data?.estado,
      stateName: data?.state_name ?? data?.estado_nome,
      country: data?.country ?? data?.pais ?? 'Brasil',
      postcode: data?.postcode ?? data?.cep,
      formattedAddress: data?.formatted_address ?? data?.formattedAddress,
      distanceKm: data?.distance_km,
      bairro: data?.bairro,
      neighborhood: data?.bairro,
      logradouro: data?.logradouro,
      street: data?.logradouro,
      complemento: data?.complemento,
      cep: data?.cep
    };
  }
}

// Export a singleton instance
export const embrapaApi = new EmbrapaApiService();
