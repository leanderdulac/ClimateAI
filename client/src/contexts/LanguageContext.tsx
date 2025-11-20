
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { Language, translations } from '../i18n/translations';

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
}

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>('pt-BR');

    useEffect(() => {
        const savedLang = localStorage.getItem('climateai-lang') as Language;
        if (savedLang && (savedLang === 'pt-BR' || savedLang === 'en-US')) {
            setLanguageState(savedLang);
        }
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('climateai-lang', lang);
    };

    const t = (key: string): string => {
        const keys = key.split('.');
        const value: any = translations[language];

        // Simple lookup for flat keys, could be extended for nested keys if needed
        // But our translations structure is currently flat/simple
        if (value[key]) {
            return value[key];
        }

        return key;
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}
