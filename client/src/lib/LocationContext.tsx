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
    // Localização padrão: São Paulo
    const defaultLocation: LocalizacaoData = {
        latitude: -23.5505,
        longitude: -46.6333,
        cidade: 'São Paulo',
        estado: 'SP',
        estado_nome: 'São Paulo',
        formattedAddress: 'São Paulo, SP, Brasil'
    };

    const [selectedLocation, setSelectedLocation] = useState<LocalizacaoData | null>(defaultLocation);
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