'use client';

import { useI18n, Language } from './i18n-provider';

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex gap-2 items-center">
      <button
        onClick={() => setLocale('ja')}
        className={`px-2 py-1 text-sm rounded transition-colors ${
          locale === 'ja'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
        }`}
        aria-label="Switch to Japanese"
      >
        日本語
      </button>
      <button
        onClick={() => setLocale('en')}
        className={`px-2 py-1 text-sm rounded transition-colors ${
          locale === 'en'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
        }`}
        aria-label="Switch to English"
      >
        EN
      </button>
    </div>
  );
}
