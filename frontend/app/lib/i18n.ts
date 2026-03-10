'use client';

import { useI18n as useI18nContext } from './i18n-provider';

export function useI18n() {
  const { t, locale } = useI18nContext();
  return { t, locale };
}
