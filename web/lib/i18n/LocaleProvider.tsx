'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  defaultLocale,
  getDictionary,
  locales,
  type Dictionary,
  type DictionaryKey,
  type Locale,
} from './index';

const LOCALE_COOKIE = 'NEXT_LOCALE';

type Vars = Record<string, string | number>;

type LocaleContextValue = {
  locale: Locale;
  dict: Dictionary;
  t: (key: DictionaryKey, vars?: Vars) => string;
  setLocale: (next: Locale) => void;
  availableLocales: readonly Locale[];
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

function format(template: string, vars?: Vars): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, key: string) =>
    key in vars ? String(vars[key]) : `{${key}}`,
  );
}

function writeLocaleCookie(locale: Locale): void {
  if (typeof document === 'undefined') return;
  const maxAge = 60 * 60 * 24 * 365;
  document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=${maxAge}; samesite=lax`;
}

export function LocaleProvider({
  initialLocale,
  children,
}: {
  initialLocale: Locale;
  children: ReactNode;
}) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    writeLocaleCookie(next);
    if (typeof document !== 'undefined') {
      document.documentElement.lang = next;
    }
  }, []);

  const dict = useMemo(() => getDictionary(locale), [locale]);

  const t = useCallback(
    (key: DictionaryKey, vars?: Vars): string =>
      format(dict[key] ?? key, vars),
    [dict],
  );

  const value = useMemo<LocaleContextValue>(
    () => ({
      locale,
      dict,
      t,
      setLocale,
      availableLocales: locales,
    }),
    [locale, dict, t, setLocale],
  );

  return (
    <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    return {
      locale: defaultLocale,
      dict: getDictionary(defaultLocale),
      t: (key, vars) => format(getDictionary(defaultLocale)[key] ?? key, vars),
      setLocale: () => {},
      availableLocales: locales,
    };
  }
  return ctx;
}

export function useT(): (key: DictionaryKey, vars?: Vars) => string {
  return useLocale().t;
}
