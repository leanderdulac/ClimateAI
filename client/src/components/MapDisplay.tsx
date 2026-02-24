import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import { useLocation } from '@/lib/LocationContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, Thermometer, Droplets, Wind, MapPin } from 'lucide-react';
import { embrapaApi } from '@/lib/api';
import { useTranslation } from '@/hooks/useTranslation';

// Fix for default marker icon
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import markerIcon2xPng from "leaflet/dist/images/marker-icon-2x.png";
import markerShadowPng from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = new Icon({
    iconUrl: markerIconPng,
    iconRetinaUrl: markerIcon2xPng,
    shadowUrl: markerShadowPng,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

function FlyToLocation({ coords }: { coords: [number, number] }) {
    const map = useMap();
    useEffect(() => {
        map.flyTo(coords, 10, {
            duration: 2
        });
    }, [coords, map]);
    return null;
}

interface WeatherInfo {
    temperature: number;
    precipitation: number;
    humidity: number;
    windSpeed?: number;
}

export function MapDisplay() {
    const { selectedLocation } = useLocation();
    const { t } = useTranslation();
    const [weather, setWeather] = useState<WeatherInfo | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        async function fetchWeather() {
            if (!selectedLocation) return;

            setLoading(true);
            try {
                const data = await embrapaApi.getDadosAtuais(
                    selectedLocation.latitude,
                    selectedLocation.longitude
                );

                setWeather({
                    temperature: data.temperatura,
                    precipitation: data.precipitacao,
                    humidity: data.umidade,
                    windSpeed: data.vento_velocidade
                });
            } catch (error) {
                console.error("Error fetching weather for map:", error);
            } finally {
                setLoading(false);
            }
        }

        fetchWeather();
    }, [selectedLocation]);

    if (!selectedLocation) {
        return null;
    }

    const position: [number, number] = [selectedLocation.latitude, selectedLocation.longitude];

    return (
        <Card className="w-full overflow-hidden glass-card border-0 shadow-2xl group">
            <CardHeader className="relative overflow-hidden">
                {/* Gradient background */}
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 opacity-90"></div>

                {/* Pattern overlay */}
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20"></div>

                <CardTitle className="flex items-center gap-3 text-xl font-bold text-white relative z-10">
                    <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
                        <Globe className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex-1">
                        <div className="text-sm font-normal text-white/80 mb-1">
                            {t('map.satelliteView') || 'Visualização de Satélite'}
                        </div>
                        <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-white/80" />
                            <span className="font-bold">{selectedLocation.cidade}, {selectedLocation.estado}</span>
                        </div>
                    </div>
                </CardTitle>
            </CardHeader>

            <CardContent className="p-0 relative h-[500px] overflow-hidden">
                {/* Map container with rounded corners */}
                <div className="absolute inset-0 rounded-b-2xl overflow-hidden">
                    <MapContainer
                        key={`${selectedLocation.latitude}-${selectedLocation.longitude}`}
                        center={position}
                        zoom={10}
                        style={{ height: '100%', width: '100%' }}
                        scrollWheelZoom={false}
                        className="z-10"
                    >
                        {/* Esri World Imagery for Satellite View */}
                        <TileLayer
                            attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        />

                        {/* Hybrid Labels */}
                        <TileLayer
                            attribution='Tiles &copy; Esri'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                        />

                        <Marker position={position} icon={defaultIcon}>
                            <Popup className="min-w-[250px]">
                                <div className="p-3">
                                    <h3 className="font-black text-xl mb-3 bg-gradient-to-r from-cyan-600 to-emerald-600 bg-clip-text text-transparent">
                                        {selectedLocation.cidade}
                                    </h3>

                                    {loading ? (
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                            <div className="animate-spin h-4 w-4 border-2 border-cyan-500 border-t-transparent rounded-full"></div>
                                            <p>Carregando dados...</p>
                                        </div>
                                    ) : weather ? (
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-red-50 to-orange-50 rounded-lg">
                                                <div className="p-2 bg-red-100 rounded-lg">
                                                    <Thermometer className="h-5 w-5 text-red-600" />
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-600 font-medium">Temperatura</p>
                                                    <p className="text-lg font-black text-red-700">{typeof weather.temperature === 'number' ? weather.temperature.toFixed(1) : '--'}°C</p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg">
                                                <div className="p-2 bg-blue-100 rounded-lg">
                                                    <Droplets className="h-5 w-5 text-blue-600" />
                                                </div>
                                                <div>
                                                    <p className="text-xs text-gray-600 font-medium">Precipitação / Umidade</p>
                                                    <p className="text-lg font-black text-blue-700">
                                                        {typeof weather.precipitation === 'number' ? weather.precipitation.toFixed(1) : '--'} mm
                                                        <span className="text-sm font-normal text-gray-500 ml-2">{typeof weather.humidity === 'number' ? `(${weather.humidity}%)` : ''}</span>
                                                    </p>
                                                </div>
                                            </div>

                                            {weather.windSpeed !== undefined && (
                                                <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-slate-50 to-gray-50 rounded-lg">
                                                    <div className="p-2 bg-slate-100 rounded-lg">
                                                        <Wind className="h-5 w-5 text-slate-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-gray-600 font-medium">Velocidade do Vento</p>
                                                        <p className="text-lg font-black text-slate-700">{typeof weather.windSpeed === 'number' ? weather.windSpeed.toFixed(1) : '--'} km/h</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-sm text-gray-500 text-center py-4">Dados indisponíveis</p>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                        <FlyToLocation coords={position} />
                    </MapContainer>
                </div>

                {/* Decorative gradient overlay at bottom */}
                <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-black/20 to-transparent pointer-events-none z-20"></div>
            </CardContent>
        </Card>
    );
}
