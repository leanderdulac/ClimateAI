// Real API service for backend integration
import axios from 'axios';

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
    try {
      return await this.apiGet('/clima/historico', {
        latitude,
        longitude,
        data_inicio: startDate,
        data_fim: endDate
      });
    } catch (error) {
      // Fallback para dados mock
      console.log('Usando dados climáticos mock');
      const days = Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24));
      return mockClimateData(Math.min(days, 365));
    }
  }

  async getCurrentClimate(latitude: number, longitude: number): Promise<ClimateData> {
    try {
      return await this.apiGet('/clima/atual', {
        latitude,
        longitude
      });
    } catch (error) {
      // Fallback para dados mock
      console.log('Usando clima atual mock');
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
      const location = await this.apiGet(`/localizacao/cep/${sanitized}`);
      return this.normalizeLocation(location);
    } catch (error) {
      // Fallback para dados mock
      console.log('Usando localização por CEP mock');
      return mockLocationData(-23.5505, -46.6333);
    }
  }

  async getLocationByCity(city: string, state: string): Promise<LocationData> {
    try {
      const location = await this.apiGet('/localizacao/cidade', {
        cidade: city,
        estado: state.toUpperCase()
      });
      return this.normalizeLocation(location);
    } catch (error) {
      // Fallback para dados mock
      console.log('Usando localização por cidade mock');
      return { ...mockLocationData(-23.5505, -46.6333), city, state: state.toUpperCase() };
    }
  }

  async searchCities(term: string, state?: string): Promise<LocationData[]> {
    try {
      const cities = await this.apiGet('/localizacao/cidade/busca', {
        termo: term,
        estado: state
      });
      return Array.isArray(cities)
        ? cities.map((cityData: any) => this.normalizeLocation(cityData))
        : [];
    } catch (error) {
      // Fallback para dados mock de cidades
      console.log('Usando busca de cidades mock');
      const mockCities = [
        { city: 'São Paulo', state: 'SP', latitude: -23.5505, longitude: -46.6333 },
        { city: 'Rio de Janeiro', state: 'RJ', latitude: -22.9068, longitude: -43.1729 },
        { city: 'Belo Horizonte', state: 'MG', latitude: -19.9167, longitude: -43.9345 },
        { city: 'Brasília', state: 'DF', latitude: -15.7942, longitude: -47.8822 },
        { city: 'Curitiba', state: 'PR', latitude: -25.4284, longitude: -49.2733 }
      ].filter(c => 
        c.city.toLowerCase().includes(term.toLowerCase()) ||
        (state && c.state === state.toUpperCase())
      );
      
      return mockCities.map(c => ({
        ...mockLocationData(c.latitude, c.longitude),
        city: c.city,
        state: c.state,
        stateName: c.city
      }));
    }
  }

  async getWeatherForecast(latitude: number, longitude: number, days: number = 7): Promise<ForecastData[]> {
    const response = await this.apiGet('/clima/previsao', {
      latitude,
      longitude,
      dias: days
    }) as any;

    // O backend retorna { previsao: [...], ... }, então extraímos o array
    const forecastArray = response.previsao || response;
    return Array.isArray(forecastArray) ? forecastArray : [];
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
