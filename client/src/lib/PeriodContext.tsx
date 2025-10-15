import { createContext, useContext, useState, ReactNode } from 'react';

export type PeriodType = 7 | 30 | 90;

interface PeriodContextType {
    selectedPeriod: PeriodType;
    setSelectedPeriod: (period: PeriodType) => void;
}

const PeriodContext = createContext<PeriodContextType | undefined>(undefined);

interface PeriodProviderProps {
    children: ReactNode;
}

export function PeriodProvider({ children }: PeriodProviderProps) {
    const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>(30);

    return (
        <PeriodContext.Provider value={{ selectedPeriod, setSelectedPeriod }}>
            {children}
        </PeriodContext.Provider>
    );
}

export function usePeriod() {
    const context = useContext(PeriodContext);
    if (context === undefined) {
        throw new Error('usePeriod must be used within a PeriodProvider');
    }
    return context;
}