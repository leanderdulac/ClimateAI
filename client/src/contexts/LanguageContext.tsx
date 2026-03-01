
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { Language, translations } from '../i18n/translations';

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string, params?: Record<string, any>) => string;
}

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const SUPPORTED_LANGUAGES: Language[] = ['pt-BR', 'en-US', 'es-419', 'zh-CN'];

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>('pt-BR');

    useEffect(() => {
        const savedLang = localStorage.getItem('climatewise-lang') as Language;
        if (savedLang && SUPPORTED_LANGUAGES.includes(savedLang)) {
            setLanguageState(savedLang);
        }
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('climatewise-lang', lang);
    };

    const t = (key: string, params?: Record<string, any>): string => {
        let text = '';
        const value: any = translations[language];

        if (value && value[key]) {
            text = value[key];
        } else {
            // Fallback to en-US
            const fallback: any = translations['en-US'];
            if (fallback && fallback[key]) {
                text = fallback[key];
            } else {
                return key;
            }
        }

        if (params) {
            Object.entries(params).forEach(([k, v]) => {
                text = text.replace(new RegExp(`{{${k}}}`, 'g'), String(v));
            });
        }

        return text;
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}
