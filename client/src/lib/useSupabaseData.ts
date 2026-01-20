/**
 * Supabase Data Hooks for ClimateAI
 * Provides React hooks for CRUD operations on all database tables
 */

import { useState, useEffect, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from './supabase';
import { useAuth } from './AuthContext';

// Types
export interface Location {
    id: string;
    name: string;
    address?: string;
    city?: string;
    state?: string;
    country?: string;
    postal_code?: string;
    latitude?: number;
    longitude?: number;
    climate_zone?: string;
    risk_zone?: string;
    created_at: string;
    updated_at: string;
}

export interface Policy {
    id: string;
    user_id?: string;
    location_id?: string;
    policy_number: string;
    policy_type: 'crop' | 'property' | 'livestock' | 'parametric' | 'comprehensive';
    status: 'draft' | 'pending' | 'active' | 'expired' | 'cancelled' | 'claimed';
    coverage_amount: number;
    deductible: number;
    premium: number;
    premium_frequency: string;
    effective_date: string;
    expiration_date: string;
    risk_score?: number;
    risk_level?: string;
    climate_risk_factor?: number;
    base_premium?: number;
    loading_factor?: number;
    discount_factor?: number;
    pricing_model?: string;
    pricing_details?: Record<string, any>;
    notes?: string;
    documents?: any[];
    created_at: string;
    updated_at: string;
    // Relations
    locations?: Location;
}

export interface Claim {
    id: string;
    policy_id: string;
    user_id?: string;
    claim_number: string;
    claim_type: 'weather_damage' | 'drought' | 'flood' | 'hail' | 'frost' | 'fire' | 'pest' | 'disease' | 'other';
    status: 'reported' | 'under_review' | 'approved' | 'partially_approved' | 'denied' | 'paid' | 'closed';
    event_date: string;
    event_description?: string;
    claimed_amount: number;
    approved_amount?: number;
    paid_amount?: number;
    damage_percentage?: number;
    documents?: any[];
    photos?: any[];
    weather_data?: Record<string, any>;
    reported_at: string;
    created_at: string;
    updated_at: string;
    // Relations
    policies?: Policy;
}

export interface ClimateData {
    id: string;
    location_id?: string;
    latitude?: number;
    longitude?: number;
    recorded_date: string;
    temperature_avg?: number;
    temperature_max?: number;
    temperature_min?: number;
    precipitation?: number;
    humidity?: number;
    wind_speed?: number;
    is_extreme_event: boolean;
    extreme_event_type?: string;
    source: string;
    raw_data?: Record<string, any>;
    created_at: string;
}

export interface RiskAssessment {
    id: string;
    policy_id: string;
    assessment_type: string;
    assessment_date: string;
    overall_risk_score?: number;
    climate_risk_score?: number;
    risk_level?: string;
    recommended_premium?: number;
    recommendations?: any[];
    input_data?: Record<string, any>;
    output_data?: Record<string, any>;
    created_at: string;
}

export interface PricingHistory {
    id: string;
    policy_id: string;
    calculation_date: string;
    pricing_model: string;
    base_premium?: number;
    risk_loading?: number;
    final_premium: number;
    model_weights?: Record<string, any>;
    model_results?: Record<string, any>;
    confidence_level?: number;
    created_at: string;
}

// Generic hook result type
interface UseDataResult<T> {
    data: T[];
    loading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
    create: (item: Partial<T>) => Promise<T | null>;
    update: (id: string, item: Partial<T>) => Promise<T | null>;
    remove: (id: string) => Promise<boolean>;
}

// Generic data hook factory
function createDataHook<T extends { id: string }>(tableName: string) {
    return function useData(filters?: Record<string, any>): UseDataResult<T> {
        const [data, setData] = useState<T[]>([]);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState<string | null>(null);
        const { user } = useAuth();

        const refresh = useCallback(async () => {
            if (!isSupabaseConfigured() || !supabase) {
                setLoading(false);
                setError('Supabase não configurado');
                return;
            }

            setLoading(true);
            setError(null);

            try {
                let query = supabase.from(tableName).select('*');

                if (filters) {
                    Object.entries(filters).forEach(([key, value]) => {
                        query = query.eq(key, value);
                    });
                }

                const { data: result, error: queryError } = await query.order('created_at', { ascending: false });

                if (queryError) throw queryError;
                setData(result || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao carregar dados');
            } finally {
                setLoading(false);
            }
        }, [filters, user]);

        useEffect(() => {
            refresh();
        }, [refresh]);

        const create = async (item: Partial<T>): Promise<T | null> => {
            if (!supabase) return null;

            try {
                const { data: result, error: insertError } = await supabase
                    .from(tableName)
                    .insert(item)
                    .select()
                    .single();

                if (insertError) throw insertError;

                setData(prev => [result as T, ...prev]);
                return result as T;
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao criar');
                return null;
            }
        };

        const update = async (id: string, item: Partial<T>): Promise<T | null> => {
            if (!supabase) return null;

            try {
                const { data: result, error: updateError } = await supabase
                    .from(tableName)
                    .update(item)
                    .eq('id', id)
                    .select()
                    .single();

                if (updateError) throw updateError;

                setData(prev => prev.map(d => d.id === id ? result as T : d));
                return result as T;
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao atualizar');
                return null;
            }
        };

        const remove = async (id: string): Promise<boolean> => {
            if (!supabase) return false;

            try {
                const { error: deleteError } = await supabase
                    .from(tableName)
                    .delete()
                    .eq('id', id);

                if (deleteError) throw deleteError;

                setData(prev => prev.filter(d => d.id !== id));
                return true;
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao remover');
                return false;
            }
        };

        return { data, loading, error, refresh, create, update, remove };
    };
}

// Exported hooks
export const useLocations = createDataHook<Location>('locations');
export const useClaims = createDataHook<Claim>('claims');
export const useClimateData = createDataHook<ClimateData>('climate_data');
export const useRiskAssessments = createDataHook<RiskAssessment>('risk_assessments');
export const usePricingHistory = createDataHook<PricingHistory>('pricing_history');

// Custom hook for policies with user filtering
export function usePolicies(filters?: Record<string, any>): UseDataResult<Policy> {
    const [data, setData] = useState<Policy[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { user } = useAuth();

    const refresh = useCallback(async () => {
        if (!isSupabaseConfigured() || !supabase) {
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            let query = supabase
                .from('policies')
                .select('*, locations(name, city, state)');

            // Filter by current user if authenticated
            if (user) {
                query = query.eq('user_id', user.id);
            }

            if (filters) {
                Object.entries(filters).forEach(([key, value]) => {
                    query = query.eq(key, value);
                });
            }

            const { data: result, error: queryError } = await query.order('created_at', { ascending: false });

            if (queryError) throw queryError;
            setData(result || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar apólices');
        } finally {
            setLoading(false);
        }
    }, [filters, user]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const create = async (item: Partial<Policy>): Promise<Policy | null> => {
        if (!supabase || !user) return null;

        try {
            const policyData = {
                ...item,
                user_id: user.id,
            };

            const { data: result, error: insertError } = await supabase
                .from('policies')
                .insert(policyData)
                .select('*, locations(name, city, state)')
                .single();

            if (insertError) throw insertError;

            setData(prev => [result as Policy, ...prev]);
            return result as Policy;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar apólice');
            return null;
        }
    };

    const update = async (id: string, item: Partial<Policy>): Promise<Policy | null> => {
        if (!supabase) return null;

        try {
            const { data: result, error: updateError } = await supabase
                .from('policies')
                .update(item)
                .eq('id', id)
                .select('*, locations(name, city, state)')
                .single();

            if (updateError) throw updateError;

            setData(prev => prev.map(d => d.id === id ? result as Policy : d));
            return result as Policy;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao atualizar apólice');
            return null;
        }
    };

    const remove = async (id: string): Promise<boolean> => {
        if (!supabase) return false;

        try {
            const { error: deleteError } = await supabase
                .from('policies')
                .delete()
                .eq('id', id);

            if (deleteError) throw deleteError;

            setData(prev => prev.filter(d => d.id !== id));
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao remover apólice');
            return false;
        }
    };

    return { data, loading, error, refresh, create, update, remove };
}

// Dashboard stats hook
export function useDashboardStats() {
    const [stats, setStats] = useState({
        totalPolicies: 0,
        activePolicies: 0,
        totalClaims: 0,
        pendingClaims: 0,
        totalCoverage: 0,
        totalPremium: 0,
    });
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        if (!isSupabaseConfigured() || !supabase || !user) {
            setLoading(false);
            return;
        }

        const fetchStats = async () => {
            try {
                // Get policies stats
                const { data: policies } = await supabase
                    .from('policies')
                    .select('status, coverage_amount, premium')
                    .eq('user_id', user.id);

                // Get claims stats
                const { data: claims } = await supabase
                    .from('claims')
                    .select('status')
                    .eq('user_id', user.id);

                if (policies) {
                    setStats({
                        totalPolicies: policies.length,
                        activePolicies: policies.filter(p => p.status === 'active').length,
                        totalClaims: claims?.length || 0,
                        pendingClaims: claims?.filter(c => c.status === 'under_review').length || 0,
                        totalCoverage: policies.reduce((sum, p) => sum + (p.coverage_amount || 0), 0),
                        totalPremium: policies.reduce((sum, p) => sum + (p.premium || 0), 0),
                    });
                }
            } catch (err) {
                console.error('Error fetching dashboard stats:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [user]);

    return { stats, loading };
}

// Climate data for a specific location
export function useLocationClimateData(locationId: string | null) {
    const [data, setData] = useState<ClimateData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!isSupabaseConfigured() || !supabase || !locationId) {
            setLoading(false);
            return;
        }

        const fetchData = async () => {
            setLoading(true);
            try {
                const { data: result, error: queryError } = await supabase
                    .from('climate_data')
                    .select('*')
                    .eq('location_id', locationId)
                    .order('recorded_date', { ascending: false })
                    .limit(365);

                if (queryError) throw queryError;
                setData(result || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao carregar dados climáticos');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [locationId]);

    return { data, loading, error };
}
