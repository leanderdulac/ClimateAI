/**
 * Middleware de Propagação de X-Request-ID
 * Garante correlação de requisições entre Frontend → Backend → APIs Externas
 */

import { buildApiUrl } from './api';

/**
 * Gera um UUID v4 para X-Request-ID
 */
export function generateRequestId(): string {
    // UUID v4 implementation
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

/**
 * Obtém ou cria um X-Request-ID para uma requisição
 * Se já existir no contexto da sessão, reutiliza; caso contrário, cria um novo
 */
export function getOrCreateRequestId(): string {
    const storageKey = 'climatewise_request_id';
    
    // Tenta obter do sessionStorage (mesma aba/browser)
    let requestId = sessionStorage.getItem(storageKey);
    
    if (!requestId) {
        requestId = generateRequestId();
        sessionStorage.setItem(storageKey, requestId);
    }
    
    return requestId;
}

/**
 * Limpa o X-Request-ID atual (útil após completar uma operação)
 */
export function clearRequestId(): void {
    sessionStorage.removeItem('climatewise_request_id');
}

/**
 * Headers padrão para todas as requisições HTTP
 * Inclui X-Request-ID para correlação de traces
 */
export function getDefaultHeaders(): HeadersInit {
    const requestId = getOrCreateRequestId();
    const accessToken = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        'X-Correlation-ID': requestId,
    };

    if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
    }

    return headers;
}

/**
 * Extrai X-Request-ID de uma resposta HTTP
 */
export function getRequestIdFromResponse(response: Response): string | null {
    return response.headers.get('X-Request-ID') || 
           response.headers.get('X-Correlation-ID') || 
           null;
}

/**
 * Wrapper para fetch com propagação automática de X-Request-ID
 * 
 * Uso:
 *   const response = await fetchWithTracking('/api/v1/endpoint', {
 *     method: 'POST',
 *     body: JSON.stringify(data)
 *   });
 */
export async function fetchWithTracking(
    input: RequestInfo | URL,
    init?: RequestInit
): Promise<Response> {
    const defaultHeaders = getDefaultHeaders();
    const requestId = (defaultHeaders as Record<string, string>)['X-Request-ID'];
    
    // Merge headers
    const mergedHeaders: Record<string, string> = { ...defaultHeaders };
    
    if (init?.headers) {
        if (init.headers instanceof Headers) {
            init.headers.forEach((value, key) => {
                mergedHeaders[key] = value;
            });
        } else if (Array.isArray(init.headers)) {
            init.headers.forEach(([key, value]) => {
                mergedHeaders[key] = value;
            });
        } else {
            Object.assign(mergedHeaders, init.headers);
        }
    }
    
    // Log para debugging (em desenvolvimento)
    if (import.meta.env.DEV) {
        console.debug(`[RequestID] ${requestId} → ${typeof input === 'string' ? input : input.toString()}`);
    }
    
    // Adicionar timestamp para métricas de performance
    const startTime = performance.now();
    
    try {
        const response = await fetch(input, {
            ...init,
            headers: mergedHeaders,
        });
        
        // Log de performance
        const duration = performance.now() - startTime;
        if (import.meta.env.DEV && duration > 1000) {
            console.warn(`[RequestID] ${requestId} - Slow response: ${duration.toFixed(0)}ms`);
        }
        
        // Extrair Request-ID da resposta para validação
        const responseRequestId = getRequestIdFromResponse(response);
        if (responseRequestId && responseRequestId !== requestId) {
            console.debug(`[RequestID] Response ID mismatch: sent ${requestId}, received ${responseRequestId}`);
        }
        
        return response;
    } catch (error) {
        const duration = performance.now() - startTime;
        console.error(`[RequestID] ${requestId} - Request failed after ${duration.toFixed(0)}ms:`, error);
        throw error;
    }
}

/**
 * Interceptor para Axios (se estiver usando Axios)
 * 
 * Uso:
 *   import axios from 'axios';
 *   setupAxiosInterceptor(axios);
 */
export function setupAxiosInterceptor(axiosInstance: any): void {
    // Request interceptor
    axiosInstance.interceptors.request.use(
        (config: any) => {
            const requestId = getOrCreateRequestId();
            config.headers['X-Request-ID'] = requestId;
            config.headers['X-Correlation-ID'] = requestId;
            
            if (import.meta.env.DEV) {
                console.debug(`[Axios] ${requestId} → ${config.method?.toUpperCase()} ${config.url}`);
            }
            
            return config;
        },
        (error: any) => {
            return Promise.reject(error);
        }
    );
    
    // Response interceptor
    axiosInstance.interceptors.response.use(
        (response: any) => {
            const responseRequestId = response.headers['x-request-id'] || 
                                     response.headers['x-correlation-id'];
            
            if (import.meta.env.DEV && responseRequestId) {
                console.debug(`[Axios] ← Response ${responseRequestId} (${response.status})`);
            }
            
            return response;
        },
        (error: any) => {
            const requestId = error.config?.headers?.['X-Request-ID'] || 'unknown';
            console.error(`[Axios] ${requestId} - Request failed:`, error.message);
            return Promise.reject(error);
        }
    );
}

/**
 * Hook React para obter o Request-ID atual
 * 
 * Uso:
 *   const requestId = useRequestId();
 */
export function useRequestId(): string {
    // Em um componente React, você pode usar useState para manter o requestId
    // Esta é uma versão simplificada
    return getOrCreateRequestId();
}

/**
 * Componente Provider para contexto de Request-ID
 * 
 * Uso:
 *   <RequestIDProvider>
 *     <App />
 *   </RequestIDProvider>
 */
import { createContext, useContext, useMemo } from 'react';

const RequestIDContext = createContext<string>('');

export function RequestIDProvider({ children }: { children: React.ReactNode }): JSX.Element {
    const requestId = useMemo(() => getOrCreateRequestId(), []);
    
    return (
        <RequestIDContext.Provider value={requestId}>
            {children}
        </RequestIDContext.Provider>
    );
}

export function useRequestIDContext(): string {
    const context = useContext(RequestIDContext);
    if (!context) {
        throw new Error('useRequestIDContext must be used within a RequestIDProvider');
    }
    return context;
}
