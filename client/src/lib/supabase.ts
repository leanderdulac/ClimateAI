/**
 * Supabase Client for ClimateAI Frontend
 * Provides database and authentication integration with Supabase.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Fallback credentials for production (in case env vars don't load correctly during build)
const FALLBACK_SUPABASE_URL = 'https://tyzmywhvpmdfepxdtyes.supabase.co';
const FALLBACK_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5em15d2h2cG1kZmVweGR0eWVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzAzNjcsImV4cCI6MjA4NDQ0NjM2N30.14R4jz5hzgx6u3pPnMDrnBEUmgorb0Iqlb8spQRgzaI';

// Get Supabase credentials from environment variables with fallback
// Get Supabase credentials from environment variables with fallback
// Helper to validate JWT format (header.payload.signature)
const isValidJWT = (key: string | undefined): boolean => {
    if (!key) return false;
    const parts = key.split('.');
    return parts.length === 3 && parts[2].length > 0;
};

// Get Supabase credentials - prefer Env Var IF valid, otherwise use Fallback
const envKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || FALLBACK_SUPABASE_URL;

// If Env Var is truncated (common Vercel issue), use fallback
const supabaseAnonKey = isValidJWT(envKey) ? envKey : FALLBACK_SUPABASE_ANON_KEY;

console.log('Supabase Config:', {
    url: supabaseUrl,
    keyLength: supabaseAnonKey?.length,
    isFallback: supabaseAnonKey === FALLBACK_SUPABASE_ANON_KEY
});

// Validate configuration
export const isSupabaseConfigured = (): boolean => {
    return Boolean(supabaseUrl && supabaseAnonKey);
};

// Create Supabase client
let supabaseClient: SupabaseClient | null = null;

export const getSupabaseClient = (): SupabaseClient | null => {
    if (supabaseClient) {
        return supabaseClient;
    }

    if (!isSupabaseConfigured()) {
        console.warn('Supabase not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
        return null;
    }

    try {
        supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
            auth: {
                autoRefreshToken: true,
                persistSession: true,
                detectSessionInUrl: true,
            },
        });
        return supabaseClient;
    } catch (error) {
        console.error('Failed to create Supabase client:', error);
        return null;
    }
};

// Export a default client instance
export const supabase = isSupabaseConfigured()
    ? createClient(supabaseUrl, supabaseAnonKey, {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true,
        },
    })
    : null;

// Auth helper functions
export const signUp = async (email: string, password: string) => {
    const client = getSupabaseClient();
    if (!client) return { error: { message: 'Supabase not configured' } };

    const { data, error } = await client.auth.signUp({
        email,
        password,
    });

    return { data, error };
};

export const signIn = async (email: string, password: string) => {
    const client = getSupabaseClient();
    if (!client) return { error: { message: 'Supabase not configured' } };

    const { data, error } = await client.auth.signInWithPassword({
        email,
        password,
    });

    return { data, error };
};

export const signOut = async () => {
    const client = getSupabaseClient();
    if (!client) return { error: { message: 'Supabase not configured' } };

    const { error } = await client.auth.signOut();
    return { error };
};

export const getCurrentUser = async () => {
    const client = getSupabaseClient();
    if (!client) return null;

    const { data: { user } } = await client.auth.getUser();
    return user;
};

export const getSession = async () => {
    const client = getSupabaseClient();
    if (!client) return null;

    const { data: { session } } = await client.auth.getSession();
    return session;
};

// Subscribe to auth state changes
export const onAuthStateChange = (callback: (event: string, session: any) => void) => {
    const client = getSupabaseClient();
    if (!client) return { data: { subscription: { unsubscribe: () => { } } } };

    return client.auth.onAuthStateChange(callback);
};

// Database helper functions
export const queryTable = async <T>(
    table: string,
    filters?: Record<string, unknown>,
    limit = 100
): Promise<T[]> => {
    const client = getSupabaseClient();
    if (!client) return [];

    let query = client.from(table).select('*');

    if (filters) {
        Object.entries(filters).forEach(([column, value]) => {
            query = query.eq(column, value);
        });
    }

    const { data, error } = await query.limit(limit);

    if (error) {
        console.error(`Error querying ${table}:`, error);
        return [];
    }

    return (data || []) as T[];
};

export const insertRow = async <T>(table: string, data: Partial<T>): Promise<T | null> => {
    const client = getSupabaseClient();
    if (!client) return null;

    const { data: result, error } = await client.from(table).insert(data).select().single();

    if (error) {
        console.error(`Error inserting into ${table}:`, error);
        return null;
    }

    return result as T;
};

export const updateRow = async <T>(
    table: string,
    idColumn: string,
    idValue: unknown,
    data: Partial<T>
): Promise<T | null> => {
    const client = getSupabaseClient();
    if (!client) return null;

    const { data: result, error } = await client
        .from(table)
        .update(data)
        .eq(idColumn, idValue)
        .select()
        .single();

    if (error) {
        console.error(`Error updating ${table}:`, error);
        return null;
    }

    return result as T;
};

export const deleteRow = async (table: string, idColumn: string, idValue: unknown): Promise<boolean> => {
    const client = getSupabaseClient();
    if (!client) return false;

    const { error } = await client.from(table).delete().eq(idColumn, idValue);

    if (error) {
        console.error(`Error deleting from ${table}:`, error);
        return false;
    }

    return true;
};

// Types for common database tables
export interface User {
    id: string;
    email: string;
    name?: string;
    role?: string;
    created_at: string;
    updated_at: string;
}

export interface Policy {
    id: string;
    user_id: string;
    name: string;
    coverage_amount: number;
    premium: number;
    status: 'active' | 'pending' | 'expired';
    location_lat?: number;
    location_lng?: number;
    created_at: string;
    updated_at: string;
}

export interface ClimateData {
    id: string;
    policy_id?: string;
    latitude: number;
    longitude: number;
    temperature?: number;
    precipitation?: number;
    humidity?: number;
    date: string;
    source: string;
    created_at: string;
}
