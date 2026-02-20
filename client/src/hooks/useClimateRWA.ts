import { useState, useCallback } from 'react';

interface AuditTrail {
    tx_hash: string;
    satellite_evidence: {
        source: string;
        ndvi_at_payout: number;
        anomaly_detected: boolean;
    };
    actuarial_proof: {
        severity_score: number;
        monte_carlo_confidence: string;
    };
    timestamp: string;
    status: string;
}

interface VaultStats {
    tvl_usdc: number;
    active_collateral: number;
    current_apy: string;
    total_claims_paid: number;
    investor_count: number;
}

export const useClimateRWA = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchAuditTrail = useCallback(async (txHash: string): Promise<AuditTrail | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/v1/transparency/audit/${txHash}`);
            if (!response.ok) throw new Error('Failed to fetch audit trail');
            return await response.json();
        } catch (err: any) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchVaultStats = useCallback(async (): Promise<VaultStats | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/transparency/vault/stats');
            if (!response.ok) throw new Error('Failed to fetch vault stats');
            return await response.json();
        } catch (err: any) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const offsetCarbon = useCallback(async (amountUsd: number, beneficiaryAddress: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/carbon/offset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount_usd: amountUsd, beneficiary_address: beneficiaryAddress }),
            });
            if (!response.ok) throw new Error('Carbon offset failed');
            return await response.json();
        } catch (err: any) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        fetchAuditTrail,
        fetchVaultStats,
        offsetCarbon,
    };
};
