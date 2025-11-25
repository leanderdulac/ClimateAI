import { createContext, useContext, useState, ReactNode } from 'react';
import type { LocalizacaoData } from '@/lib/api';

interface LocationContextType {
    selectedLocation: LocalizacaoData | null;
    setSelectedLocation: (location: LocalizacaoData | null) => void;
    isLoadingLocation: boolean;
    setIsLoadingLocation: (loading: boolean) => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export function LocationProvider({ children }: { children: ReactNode }) {
    // Inicialmente sem localização - o usuário deve selecionar
    const [selectedLocation, setSelectedLocation] = useState<LocalizacaoData | null>(null);
    const [isLoadingLocation, setIsLoadingLocation] = useState(false);

    return (
        <LocationContext.Provider
            value={{
                selectedLocation,
                setSelectedLocation,
                isLoadingLocation,
                setIsLoadingLocation,
            }}
        >
            {children}
        </LocationContext.Provider>
    );
}

export function useLocation() {
    const context = useContext(LocationContext);
    if (context === undefined) {
        throw new Error('useLocation must be used within a LocationProvider');
    }
    return context;
}
