'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import jaTranslations from '../../public/locales/ja/translation.json';
import enTranslations from '../../public/locales/en/translation.json';

type TranslationKeys = Record<string, unknown>;
type Language = 'ja' | 'en';

interface I18nContextType {
  locale: Language;
  setLocale: (lang: Language) => void;
  t: (key: string) => string;
}

const translations: Record<Language, TranslationKeys> = {
  ja: jaTranslations as TranslationKeys,
  en: enTranslations as TranslationKeys,
};

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Language>('ja');

  useEffect(() => {
    // Load saved locale from localStorage
    const saved = localStorage.getItem('locale') as Language | null;
    if (saved && (saved === 'ja' || saved === 'en')) {
      setLocale(saved);
    }
  }, []);

  const handleSetLocale = (lang: Language) => {
    setLocale(lang);
    localStorage.setItem('locale', lang);
  };

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: unknown = translations[locale];

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = (value as Record<string, unknown>)[k];
      } else {
        console.warn(`Translation missing: ${key}`);
        return key;
      }
    }

    return typeof value === 'string' ? value : key;
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale: handleSetLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}

export type { Language };
