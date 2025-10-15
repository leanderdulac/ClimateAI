import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { fetchWeatherApi } from 'openmeteo'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export interface WeatherData {
  current: {
    time: Date
    temperature_2m: number
    relative_humidity_2m: number
    apparent_temperature: number
    precipitation: number
    weather_code: number
    wind_speed_10m: number
    wind_direction_10m: number
  }
  daily: {
    time: Date[]
    temperature_2m_max: number[]
    temperature_2m_min: number[]
    precipitation_sum: number[]
    precipitation_probability_max: number[]
    wind_speed_10m_max: number[]
    weather_code: number[]
  }
  historical?: {
    time: Date[]
    temperature_2m: number[]
  }
  coordinates: {
    latitude: number
    longitude: number
    elevation: number
    timezone: string
    timezone_abbreviation: string
    timezone_offset_sec: number
  }
}

export async function fetchWeatherData(
  latitude: number,
  longitude: number,
  includeHistorical: boolean = false,
  historicalDays: number = 15
): Promise<WeatherData> {
  // Fetch forecast data
  const forecastParams = {
    latitude,
    longitude,
    current: [
      "temperature_2m",
      "relative_humidity_2m",
      "apparent_temperature",
      "precipitation",
      "weather_code",
      "wind_speed_10m",
      "wind_direction_10m"
    ],
    daily: [
      "temperature_2m_max",
      "temperature_2m_min",
      "precipitation_sum",
      "precipitation_probability_max",
      "wind_speed_10m_max",
      "weather_code"
    ],
    timezone: "America/Sao_Paulo",
    past_days: 0,
    forecast_days: 16
  }

  const forecastResponses = await fetchWeatherApi("https://api.open-meteo.com/v1/forecast", forecastParams)
  const forecastResponse = forecastResponses[0]

  // Process first location
  const utcOffsetSeconds = forecastResponse.utcOffsetSeconds()
  const current = forecastResponse.current()!
  const daily = forecastResponse.daily()!

  const weatherData: WeatherData = {
    current: {
      time: new Date((Number(current.time()) + utcOffsetSeconds) * 1000),
      temperature_2m: current.variables(0)!.value(),
      relative_humidity_2m: current.variables(1)!.value(),
      apparent_temperature: current.variables(2)!.value(),
      precipitation: current.variables(3)!.value(),
      weather_code: current.variables(4)!.value(),
      wind_speed_10m: current.variables(5)!.value(),
      wind_direction_10m: current.variables(6)!.value(),
    },
    daily: {
      time: [...Array((Number(daily.timeEnd()) - Number(daily.time())) / daily.interval())].map(
        (_, i) => new Date((Number(daily.time()) + i * daily.interval() + utcOffsetSeconds) * 1000)
      ),
      temperature_2m_max: Array.from(daily.variables(0)?.valuesArray() ?? []),
      temperature_2m_min: Array.from(daily.variables(1)?.valuesArray() ?? []),
      precipitation_sum: Array.from(daily.variables(2)?.valuesArray() ?? []),
      precipitation_probability_max: Array.from(daily.variables(3)?.valuesArray() ?? []),
      wind_speed_10m_max: Array.from(daily.variables(4)?.valuesArray() ?? []),
      weather_code: Array.from(daily.variables(5)?.valuesArray() ?? []),
    },
    coordinates: {
      latitude: forecastResponse.latitude(),
      longitude: forecastResponse.longitude(),
      elevation: forecastResponse.elevation(),
      timezone: forecastResponse.timezone() ?? "America/Sao_Paulo",
      timezone_abbreviation: forecastResponse.timezoneAbbreviation() ?? "BRT",
      timezone_offset_sec: utcOffsetSeconds
    }
  }

  // Fetch historical data if requested
  if (includeHistorical) {
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - historicalDays)

    const historicalParams = {
      latitude,
      longitude,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      hourly: ["temperature_2m"],
      timezone: "America/Sao_Paulo"
    }

    const historicalResponses = await fetchWeatherApi("https://archive-api.open-meteo.com/v1/archive", historicalParams)
    const historicalResponse = historicalResponses[0]
    const hourly = historicalResponse.hourly()!

    weatherData.historical = {
      time: [...Array((Number(hourly.timeEnd()) - Number(hourly.time())) / hourly.interval())].map(
        (_, i) => new Date((Number(hourly.time()) + i * hourly.interval() + utcOffsetSeconds) * 1000)
      ),
      temperature_2m: Array.from(hourly.variables(0)?.valuesArray() ?? [])
    }
  }

  return weatherData
}