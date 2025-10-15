// Limites do território brasileiro
const BRAZIL_BOUNDS = {
    north: 5.27438, // Ponto mais ao norte
    south: -33.75117, // Ponto mais ao sul
    west: -73.98502, // Ponto mais a oeste
    east: -34.79299 // Ponto mais a leste
};

export interface Coordinates {
    latitude: number;
    longitude: number;
}

export function isWithinBrazil(latitude: number, longitude: number): boolean {
    return (
        latitude <= BRAZIL_BOUNDS.north &&
        latitude >= BRAZIL_BOUNDS.south &&
        longitude <= BRAZIL_BOUNDS.east &&
        longitude >= BRAZIL_BOUNDS.west
    );
}

export function formatCoordinates(latitude: number, longitude: number): string {
    return `${Math.abs(latitude).toFixed(4)}°${latitude >= 0 ? 'N' : 'S'}, ${Math.abs(longitude).toFixed(4)}°${longitude >= 0 ? 'E' : 'W'}`;
}

// Distância entre dois pontos em km usando a fórmula de Haversine
export function getDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // Raio da Terra em km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
}

// Cache de localizações recentes
export interface SavedLocation extends Coordinates {
    name: string;
    state?: string;
    timestamp: number;
}

const RECENT_LOCATIONS_KEY = 'recentLocations';
const MAX_RECENT_LOCATIONS = 5;

export function saveRecentLocation(location: SavedLocation): void {
    const recent = getRecentLocations();
    const filtered = recent.filter(
        loc => !(loc.latitude === location.latitude && loc.longitude === location.longitude)
    );
    filtered.unshift(location);
    while (filtered.length > MAX_RECENT_LOCATIONS) {
        filtered.pop();
    }
    localStorage.setItem(RECENT_LOCATIONS_KEY, JSON.stringify(filtered));
}

export function getRecentLocations(): SavedLocation[] {
    try {
        const stored = localStorage.getItem(RECENT_LOCATIONS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}