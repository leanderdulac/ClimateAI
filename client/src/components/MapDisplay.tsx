import { useEffect, useState } from 'react';
import { CircleMarker, MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import { useLocation } from '@/lib/LocationContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, Thermometer, Droplets, Wind, MapPin } from 'lucide-react';
import { embrapaApi } from '@/lib/api';
import { weathernextApi, type BrazilGridCell } from '@/lib/api/weathernext';
import { isFeatureEnabled } from '@/lib/features';
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
    const [showHeavyRain, setShowHeavyRain] = useState(false);
    const [rainCells, setRainCells] = useState<BrazilGridCell[]>([]);

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

    useEffect(() => {
        if (!isFeatureEnabled('weathernext') || !showHeavyRain) {
            return;
        }
        let cancelled = false;
        weathernextApi
            .getBrazilGrid(2)
            .then((grid) => {
                if (!cancelled) setRainCells(grid.cells ?? []);
            })
            .catch(() => {
                if (!cancelled) setRainCells([]);
            });
        return () => {
            cancelled = true;
        };
    }, [showHeavyRain]);

    if (!selectedLocation) {
        return null;
    }

    const position: [number, number] = [selectedLocation.latitude, selectedLocation.longitude];

    return (
        <Card className="cc-card w-full overflow-hidden border-border/80 bg-card/60 backdrop-blur-xl group">
            <CardHeader className="cc-header relative overflow-hidden border-border/40">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(37,99,235,0.16),transparent_55%)]" />
                <CardTitle className="relative z-10 flex items-center gap-3 text-xl font-bold text-foreground">
                    <div className="rounded-xl bg-blue-500/10 p-2 text-blue-400">
                        <Globe className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                        <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            {t('map.satelliteView') || 'Visualização de Satélite'}
                        </div>
                        <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-primary" />
                            <span className="font-bold">{selectedLocation.cidade}, {selectedLocation.estado}</span>
                        </div>
                    </div>
                    {isFeatureEnabled('weathernext') && (
                        <button
                            type="button"
                            onClick={() => setShowHeavyRain((value) => !value)}
                            className={`relative z-10 text-xs px-3 py-1.5 rounded-full border transition-colors ${
                                showHeavyRain
                                    ? 'bg-white/25 text-white border-white/40'
                                    : 'bg-black/20 text-white/70 border-white/20'
                            }`}
                        >
                            {t('weathernext.mapLayer')}
                        </button>
                    )}
                </CardTitle>
            </CardHeader>

            <CardContent className="p-0 relative h-[500px] overflow-hidden">
                {/* Map container with rounded corners */}
                <div className="absolute inset-0 rounded-b-2xl overflow-hidden">
                    <MapContainer
                        center={position}
                        zoom={10}
                        style={{ height: '100%', width: '100%' }}
                        scrollWheelZoom={false}
                        className="z-10"
                        ref={(map) => {
                            if (map) {
                                // Add a cleanup listener for unmount
                                const originalRemove = map.remove;
                                map.remove = function() {
                                    try {
                                        this.closePopup();
                                        originalRemove.call(this);
                                    } catch (e) {
                                        console.warn("Map cleanup handled safely", e);
                                    }
                                    return this;
                                };
                            }
                        }}
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

                        {showHeavyRain &&
                            rainCells.map((cell) => (
                                <CircleMarker
                                    key={`${cell.lat}:${cell.lon}`}
                                    center={[cell.lat, cell.lon]}
                                    radius={8}
                                    pathOptions={{
                                        color: 'transparent',
                                        fillColor: cell.p_heavy_rain > 0.6 ? '#2563eb' : cell.p_heavy_rain > 0.3 ? '#22d3ee' : '#fde047',
                                        fillOpacity: 0.35 + cell.p_heavy_rain * 0.45,
                                    }}
                                >
                                    <Popup>
                                        <div className="text-sm">
                                            <div className="font-semibold">{t('weathernext.heavyRain')}</div>
                                            <div>{Math.round(cell.p_heavy_rain * 100)}%</div>
                                        </div>
                                    </Popup>
                                </CircleMarker>
                            ))}
                        <Marker position={position} icon={defaultIcon}>
                            <Popup className="min-w-[250px]">
                                <div className="p-3">
                                    <h3 className="mb-3 bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-xl font-black text-transparent">
                                        {selectedLocation.cidade}
                                    </h3>

                                    {loading ? (
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent"></div>
                                            <p>Carregando dados...</p>
                                        </div>
                                    ) : weather ? (
                                        <div className="space-y-3">
                                            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/40 p-3">
                                                <div className="rounded-lg bg-amber-500/10 p-2">
                                                    <Thermometer className="h-5 w-5 text-amber-400" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-medium text-muted-foreground">Temperatura</p>
                                                    <p className="text-lg font-black text-foreground">{typeof weather.temperature === 'number' ? weather.temperature.toFixed(1) : '--'}°C</p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/40 p-3">
                                                <div className="rounded-lg bg-blue-500/10 p-2">
                                                    <Droplets className="h-5 w-5 text-blue-400" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-medium text-muted-foreground">Precipitação / Umidade</p>
                                                    <p className="text-lg font-black text-foreground">
                                                        {typeof weather.precipitation === 'number' ? weather.precipitation.toFixed(1) : '--'} mm
                                                        <span className="ml-2 text-sm font-normal text-muted-foreground">{typeof weather.humidity === 'number' ? `(${weather.humidity}%)` : ''}</span>
                                                    </p>
                                                </div>
                                            </div>

                                            {weather.windSpeed !== undefined && (
                                                <div className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/40 p-3">
                                                    <div className="rounded-lg bg-emerald-500/10 p-2">
                                                        <Wind className="h-5 w-5 text-emerald-400" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">Velocidade do Vento</p>
                                                        <p className="text-lg font-black text-foreground">{typeof weather.windSpeed === 'number' ? weather.windSpeed.toFixed(1) : '--'} km/h</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="py-4 text-center text-sm text-muted-foreground">Dados indisponíveis</p>
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
