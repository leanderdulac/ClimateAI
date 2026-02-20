/**
 * Hook para Gerenciamento de Consentimento LGPD/GDPR
 * Gerencia cookies, localStorage e preferências de privacidade
 */

import { useState, useEffect, useCallback } from 'react';

// Tipos de consentimento
export type ConsentCategory = 'necessary' | 'analytics' | 'marketing' | 'preferences';

export interface ConsentPreferences {
    necessary: boolean;      // Sempre ativo (não pode ser desativado)
    analytics: boolean;      // Analytics e telemetria
    marketing: boolean;      // Marketing e personalização
    preferences: boolean;    // Preferências de usuário
    acceptedAt?: string;     // Timestamp de aceitação
    version?: string;        // Versão da política de privacidade
}

const CONSENT_STORAGE_KEY = 'climateai_consent';
const CONSENT_VERSION = '1.0.0';

// Consentimento padrão (apenas necessário)
const DEFAULT_CONSENT: ConsentPreferences = {
    necessary: true,
    analytics: false,
    marketing: false,
    preferences: false,
};

/**
 * Hook para gerenciamento de consentimento LGPD/GDPR
 */
export function useConsent() {
    const [consent, setConsent] = useState<ConsentPreferences>(DEFAULT_CONSENT);
    const [hasConsent, setHasConsent] = useState(false);
    const [showBanner, setShowBanner] = useState(false);

    // Carregar consentimento ao montar
    useEffect(() => {
        loadConsent();
    }, []);

    /**
     * Carregar consentimento do localStorage
     */
    const loadConsent = useCallback(() => {
        try {
            const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
            if (stored) {
                const parsed: ConsentPreferences = JSON.parse(stored);
                
                // Verificar versão da política
                if (parsed.version !== CONSENT_VERSION) {
                    // Política atualizada, precisar de novo consentimento
                    setShowBanner(true);
                    setConsent(DEFAULT_CONSENT);
                } else {
                    setConsent(parsed);
                    setHasConsent(true);
                    setShowBanner(false);
                }
            } else {
                // Primeiro acesso, mostrar banner
                setShowBanner(true);
            }
        } catch (error) {
            console.error('Error loading consent:', error);
            setShowBanner(true);
        }
    }, []);

    /**
     * Salvar consentimento no localStorage
     */
    const saveConsent = useCallback((newConsent: ConsentPreferences) => {
        try {
            const consentToSave = {
                ...newConsent,
                acceptedAt: new Date().toISOString(),
                version: CONSENT_VERSION,
            };
            localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consentToSave));
            setConsent(consentToSave);
            setHasConsent(true);
            setShowBanner(false);
            
            // Notificar sistemas de analytics
            if (consentToSave.analytics) {
                initializeAnalytics();
            } else {
                disableAnalytics();
            }
        } catch (error) {
            console.error('Error saving consent:', error);
        }
    }, []);

    /**
     * Aceitar todos os cookies
     */
    const acceptAll = useCallback(() => {
        saveConsent({
            necessary: true,
            analytics: true,
            marketing: true,
            preferences: true,
        });
    }, [saveConsent]);

    /**
     * Aceitar apenas necessários
     */
    const acceptNecessary = useCallback(() => {
        saveConsent(DEFAULT_CONSENT);
    }, [saveConsent]);

    /**
     * Personalizar consentimento
     */
    const customizeConsent = useCallback((categories: Partial<ConsentPreferences>) => {
        saveConsent({
            ...DEFAULT_CONSENT,
            ...categories,
        });
    }, [saveConsent]);

    /**
     * Retirar consentimento
     */
    const withdrawConsent = useCallback(() => {
        localStorage.removeItem(CONSENT_STORAGE_KEY);
        setConsent(DEFAULT_CONSENT);
        setHasConsent(false);
        setShowBanner(true);
        disableAnalytics();
    }, []);

    /**
     * Verificar se tem consentimento para categoria específica
     */
    const hasCategoryConsent = useCallback((category: ConsentCategory): boolean => {
        if (category === 'necessary') return true;
        return consent[category] === true;
    }, [consent]);

    return {
        consent,
        hasConsent,
        showBanner,
        setShowBanner,
        acceptAll,
        acceptNecessary,
        customizeConsent,
        withdrawConsent,
        hasCategoryConsent,
        loadConsent,
    };
}

/**
 * Inicializar analytics (apenas com consentimento)
 */
function initializeAnalytics() {
    // Aqui você inicializa Google Analytics, Mixpanel, etc.
    if (typeof window !== 'undefined') {
        console.log('Analytics initialized with consent');
        // window.gtag('consent', 'update', { ... });
    }
}

/**
 * Desativar analytics (sem consentimento)
 */
function disableAnalytics() {
    if (typeof window !== 'undefined') {
        console.log('Analytics disabled');
        // window.gtag('consent', 'update', { ... });
    }
}

/**
 * Componente Banner de Consentimento LGPD
 */
import { useState as useStateReact } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Shield, Cookie, Settings, Check, X } from 'lucide-react';

interface ConsentBannerProps {
    show: boolean;
    onAcceptAll: () => void;
    onAcceptNecessary: () => void;
    onCustomize: (categories: Partial<ConsentPreferences>) => void;
    onClose: () => void;
}

export function ConsentBanner({ 
    show, 
    onAcceptAll, 
    onAcceptNecessary, 
    onCustomize,
    onClose 
}: ConsentBannerProps) {
    const [showCustomization, setShowCustomization] = useStateReact(false);
    const [customCategories, setCustomCategories] = useStateReact<Partial<ConsentPreferences>>({
        analytics: false,
        marketing: false,
        preferences: false,
    });

    if (!show) return null;

    const handleSaveCustom = () => {
        onCustomize(customCategories);
        setShowCustomization(false);
    };

    if (showCustomization) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <Card className="max-w-md w-full animate-in fade-in zoom-in duration-200">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Settings className="h-5 w-5" />
                            Personalizar Cookies
                        </CardTitle>
                        <CardDescription>
                            Escolha quais tipos de cookies você aceita
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Necessary - Always on */}
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="space-y-0.5">
                                <Label className="font-medium">Cookies Necessários</Label>
                                <p className="text-xs text-gray-500">
                                    Essenciais para o funcionamento do site
                                </p>
                            </div>
                            <Switch checked disabled />
                        </div>

                        {/* Analytics */}
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="space-y-0.5">
                                <Label className="font-medium">Cookies Analíticos</Label>
                                <p className="text-xs text-gray-500">
                                    Nos ajudam a entender como você usa o site
                                </p>
                            </div>
                            <Switch
                                checked={customCategories.analytics}
                                onCheckedChange={(checked) => 
                                    setCustomCategories(prev => ({ ...prev, analytics: checked }))
                                }
                            />
                        </div>

                        {/* Marketing */}
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="space-y-0.5">
                                <Label className="font-medium">Cookies de Marketing</Label>
                                <p className="text-xs text-gray-500">
                                    Usados para personalizar anúncios e conteúdo
                                </p>
                            </div>
                            <Switch
                                checked={customCategories.marketing}
                                onCheckedChange={(checked) => 
                                    setCustomCategories(prev => ({ ...prev, marketing: checked }))
                                }
                            />
                        </div>

                        {/* Preferences */}
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="space-y-0.5">
                                <Label className="font-medium">Cookies de Preferências</Label>
                                <p className="text-xs text-gray-500">
                                    Lembram suas escolhas e configurações
                                </p>
                            </div>
                            <Switch
                                checked={customCategories.preferences}
                                onCheckedChange={(checked) => 
                                    setCustomCategories(prev => ({ ...prev, preferences: checked }))
                                }
                            />
                        </div>

                        <div className="flex gap-2 pt-4">
                            <Button 
                                variant="outline" 
                                onClick={() => setShowCustomization(false)}
                                className="flex-1"
                            >
                                <X className="h-4 w-4 mr-2" />
                                Cancelar
                            </Button>
                            <Button 
                                onClick={handleSaveCustom}
                                className="flex-1"
                            >
                                <Check className="h-4 w-4 mr-2" />
                                Salvar Preferências
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-50 p-4 md:p-6 animate-in slide-in-from-bottom duration-300">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                    {/* Icon and Text */}
                    <div className="flex items-start gap-3 flex-1">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <Cookie className="h-6 w-6 text-blue-600" />
                        </div>
                        <div className="space-y-2">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <Shield className="h-5 w-5" />
                                Sua Privacidade é Importante
                            </h3>
                            <p className="text-sm text-gray-600">
                                Utilizamos cookies para melhorar sua experiência. 
                                Ao aceitar todos, você concorda com nossa{' '}
                                <a 
                                    href="/privacy-policy" 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    Política de Privacidade
                                </a>{' '}
                                e{' '}
                                <a 
                                    href="/terms" 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    Termos de Uso
                                </a>.
                            </p>
                            <div className="flex flex-wrap gap-2 text-xs">
                                <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                                    ✓ Cookies Necessários
                                </span>
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded">
                                    ○ Cookies Analíticos
                                </span>
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded">
                                    ○ Cookies de Marketing
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Buttons */}
                    <div className="flex flex-wrap gap-2 md:flex-shrink-0">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={onAcceptNecessary}
                            className="min-w-[120px]"
                        >
                            <X className="h-4 w-4 mr-2" />
                            Apenas Necessários
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowCustomization(true)}
                            className="min-w-[120px]"
                        >
                            <Settings className="h-4 w-4 mr-2" />
                            Personalizar
                        </Button>
                        <Button
                            size="sm"
                            onClick={onAcceptAll}
                            className="min-w-[120px] bg-blue-600 hover:bg-blue-700"
                        >
                            <Check className="h-4 w-4 mr-2" />
                            Aceitar Todos
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}

/**
 * Hook para verificar sessão expirada (segurança)
 */
export function useSessionTimeout(timeoutMinutes: number = 30) {
    const [isExpired, setIsExpired] = useState(false);
    const [lastActivity, setLastActivity] = useState(Date.now());

    useEffect(() => {
        const updateActivity = () => {
            setLastActivity(Date.now());
            setIsExpired(false);
        };

        // Atualizar atividade em eventos do usuário
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
        events.forEach(event => {
            window.addEventListener(event, updateActivity);
        });

        // Check periódico de expiração
        const checkInterval = setInterval(() => {
            const elapsed = Date.now() - lastActivity;
            if (elapsed > timeoutMinutes * 60 * 1000) {
                setIsExpired(true);
            }
        }, 60000); // Verificar a cada minuto

        return () => {
            events.forEach(event => {
                window.removeEventListener(event, updateActivity);
            });
            clearInterval(checkInterval);
        };
    }, [timeoutMinutes, lastActivity]);

    const extendSession = useCallback(() => {
        setLastActivity(Date.now());
        setIsExpired(false);
    }, []);

    return { isExpired, extendSession, lastActivity };
}
