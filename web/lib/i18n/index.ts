import { de } from './de';
import { en, type Dictionary } from './en';
import { defaultLocale, type Locale } from './locales';

const dictionaries: Record<Locale, Dictionary> = { en, de };

export function getDictionary(locale: Locale = defaultLocale): Dictionary {
  return dictionaries[locale] ?? dictionaries[defaultLocale];
}

export function t(key: keyof Dictionary, locale: Locale = defaultLocale): string {
  return getDictionary(locale)[key];
}

export { locales, defaultLocale, localeLabels, ogLocaleMap } from './locales';
export type { Locale } from './locales';
export type { Dictionary } from './en';
