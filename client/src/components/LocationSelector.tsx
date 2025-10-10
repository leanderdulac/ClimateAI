import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MapPin, Locate, Globe, Thermometer, Droplets, Wind, Sun } from 'lucide-react';
import { embrapaApi } from '@/lib/embrapaApi';

interface Location {
  lat: number;
  lng: number;
  region?: string;
  climateZone?: string;
}

interface LocationData {
  region: string;
  climateZone: string;
}

export function LocationSelector() {
  const [location, setLocation] = useState<Location | null>(null);
  const [locationData, setLocationData] = useState<LocationData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const detectLocation = () => {
    setLoading(true);
    setError(null);
    
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        
        setLocation(newLocation);
        fetchLocationData(newLocation.lat, newLocation.lng);
      },
      (err) => {
        setError(`Unable to retrieve your location: ${err.message}`);
        setLoading(false);
      }
    );
  };

  const fetchLocationData = async (lat: number, lng: number) => {
    try {
      const data = await embrapaApi.getLocationData(lat, lng);
      setLocationData({
        region: data.region,
        climateZone: data.climateZone
      });
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch location data');
      setLoading(false);
    }
  };

  const handleManualLocation = () => {
    const latInput = document.getElementById('manual-lat') as HTMLInputElement;
    const lngInput = document.getElementById('manual-lng') as HTMLInputElement;
    
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    
    if (isNaN(lat) || isNaN(lng)) {
      setError('Please enter valid coordinates');
      return;
    }
    
    const newLocation = { lat, lng };
    setLocation(newLocation);
    fetchLocationData(lat, lng);
  };

  return (
    <Card className="overflow-hidden animate-fade-in" variant="default">
      <CardHeader className="border-none bg-gradient-to-r from-primary-500 to-primary-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-white/10 p-3">
              <MapPin className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Location Selector</CardTitle>
              <CardDescription className="text-primary-100">
                Set your location for precise climate analysis
              </CardDescription>
            </div>
          </div>
          {locationData && (
            <div className="hidden sm:flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2">
                <Globe className="h-4 w-4 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Region</div>
                  <div className="text-sm font-medium text-white">{locationData.region}</div>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2">
                <Sun className="h-4 w-4 text-primary-100" />
                <div>
                  <div className="text-sm text-primary-100">Climate</div>
                  <div className="text-sm font-medium text-white">{locationData.climateZone}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6 p-6 bg-gradient-to-b from-white to-neutral-50">
        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Button 
              onClick={detectLocation} 
              disabled={loading}
              className="flex h-14 w-full items-center justify-center gap-2"
              variant="default"
            >
              <Locate className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Detecting Location...' : 'Auto-detect Location'}
            </Button>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-neutral-500" />
                <Label className="text-sm font-medium text-neutral-700">Manual Coordinates</Label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input 
                  id="manual-lat" 
                  placeholder="-23.5505" 
                  type="number" 
                  step="any"
                  variant="outlined"
                  error={error?.includes('latitude')}
                  className="text-center"
                />
                <Input 
                  id="manual-lng" 
                  placeholder="-46.6333" 
                  type="number" 
                  step="any"
                  variant="outlined"
                  error={error?.includes('longitude')}
                  className="text-center"
                />
              </div>
              <Button 
                onClick={handleManualLocation}
                className="w-full"
                variant="secondary"
                disabled={loading}
              >
                <MapPin className="mr-2 h-4 w-4" />
                Set Location
              </Button>
            </div>
          </div>
          
          {error && (
            <div className="animate-slide-up rounded-lg bg-danger-50 px-4 py-3 text-sm text-danger-600">
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-danger-100 p-1">
                  <MapPin className="h-4 w-4" />
                </div>
                {error}
              </div>
            </div>
          )}
          
          {location && (
            <div className="animate-slide-up space-y-6 rounded-lg bg-white p-6 shadow-soft">
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-4">
                  <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
                    <MapPin className="h-5 w-5 text-primary-500" />
                    Location Details
                  </h3>
                  <div className="grid gap-3">
                    <div className="flex items-center gap-3 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                      <div>
                        <div className="text-sm text-neutral-500">Latitude</div>
                        <div className="font-medium text-neutral-900">{location.lat.toFixed(6)}°</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                      <div>
                        <div className="text-sm text-neutral-500">Longitude</div>
                        <div className="font-medium text-neutral-900">{location.lng.toFixed(6)}°</div>
                      </div>
                    </div>
                  </div>
                </div>

                {locationData && (
                  <div className="space-y-4">
                    <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900">
                      <Globe className="h-5 w-5 text-primary-500" />
                      Regional Info
                    </h3>
                    <div className="grid gap-3">
                      <div className="flex items-center gap-3 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                        <div>
                          <div className="text-sm text-neutral-500">Region</div>
                          <div className="font-medium text-neutral-900">{locationData.region}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                        <div>
                          <div className="text-sm text-neutral-500">Climate Zone</div>
                          <div className="font-medium text-neutral-900">{locationData.climateZone}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}