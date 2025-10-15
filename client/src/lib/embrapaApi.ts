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

class EmbrapaApiService {
  private async apiGet<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    try {
      const response = await axios.get(`${baseUrl}${endpoint}`, { params });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  }

  private async apiPost<T>(endpoint: string, data?: any): Promise<T> {
    try {
      const response = await axios.post(`${baseUrl}${endpoint}`, data);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  }

  async getClimateData(latitude: number, longitude: number, startDate: string, endDate: string): Promise<ClimateData[]> {
    return this.apiGet('/clima/historico', {
      latitude,
      longitude,
      data_inicio: startDate,
      data_fim: endDate
    });
  }

  async getCurrentClimate(latitude: number, longitude: number): Promise<ClimateData> {
    return this.apiGet('/clima/atual', {
      latitude,
      longitude
    });
  }

  async getLocationData(latitude: number, longitude: number): Promise<LocationData> {
    const location = await this.apiGet('/localizacao/coordenadas', {
      latitude,
      longitude
    });
    return this.normalizeLocation(location, { latitude, longitude });
  }

  async getLocationByCep(cep: string): Promise<LocationData> {
    const sanitized = cep.replace(/\D/g, '');
    const location = await this.apiGet(`/localizacao/cep/${sanitized}`);
    return this.normalizeLocation(location);
  }

  async getLocationByCity(city: string, state: string): Promise<LocationData> {
    const location = await this.apiGet('/localizacao/cidade', {
      cidade: city,
      estado: state.toUpperCase()
    });
    return this.normalizeLocation(location);
  }

  async searchCities(term: string, state?: string): Promise<LocationData[]> {
    const cities = await this.apiGet('/localizacao/cidade/busca', {
      termo: term,
      estado: state
    });
    return Array.isArray(cities)
      ? cities.map((cityData: any) => this.normalizeLocation(cityData))
      : [];
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
