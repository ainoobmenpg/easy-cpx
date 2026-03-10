'use client';

import { useState, useCallback } from 'react';
import jaTranslations from '../public/locales/ja/translation.json';

type TranslationKeys = typeof jaTranslations;

// Simple i18n implementation for Operational CPX
// Supports Japanese as primary language, expandable to other languages

const translations: Record<string, TranslationKeys> = {
  ja: jaTranslations,
};

export type Language = 'ja';

export function useTranslation(lang: Language = 'ja') {
  const [currentLang] = useState<Language>(lang);

  const t = useCallback(
    (key: string): string => {
      const keys = key.split('.');
      let value: unknown = translations[currentLang];

      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          console.warn(`Translation missing: ${key}`);
          return key;
        }
      }

      return typeof value === 'string' ? value : key;
    },
    [currentLang]
  );

  return { t, currentLang };
}

// Helper hook for getting translations without re-renders
export function getTranslation(lang: Language = 'ja') {
  return (key: string): string => {
    const keys = key.split('.');
    let value: unknown = translations[lang];

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = (value as Record<string, unknown>)[k];
      } else {
        return key;
      }
    }

    return typeof value === 'string' ? value : key;
  };
}
