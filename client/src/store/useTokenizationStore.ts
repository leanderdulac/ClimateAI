import { create } from 'zustand';

interface TokenizationState {
    pendingTokenizationData: {
        tipo: string;
        latitude: string;
        longitude: string;
        intensidade: string;
        probabilidade: string;
        descricao: string;
        nivel_alerta: string;
        token_supply: number;
        riskFactors?: Record<string, number>;
    } | null;
    setPendingTokenizationData: (data: TokenizationState['pendingTokenizationData']) => void;
    clearPendingTokenizationData: () => void;
}

export const useTokenizationStore = create<TokenizationState>((set) => ({
    pendingTokenizationData: null,
    setPendingTokenizationData: (data) => set({ pendingTokenizationData: data }),
    clearPendingTokenizationData: () => set({ pendingTokenizationData: null }),
}));
