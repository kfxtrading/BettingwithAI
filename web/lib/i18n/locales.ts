export const locales = ['en', 'de', 'fr', 'it', 'es'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';

export const localeLabels: Record<Locale, string> = {
  en: 'English',
  de: 'Deutsch',
  fr: 'Français',
  it: 'Italiano',
  es: 'Español',
};

/** Canonical OpenGraph locale per language. */
export const ogLocaleMap: Record<Locale, string> = {
  en: 'en_US',
  de: 'de_DE',
  fr: 'fr_FR',
  it: 'it_IT',
  es: 'es_ES',
};

/**
 * Region-targeted hreflang tags.
 * Each BCP-47 tag maps to the Locale whose content it should serve.
 * Used to signal Google which country/region variants we target
 * without forking content for every region.
 */
export const hreflangRegions: Record<string, Locale> = {
  // English (global + anglophone markets)
  'en': 'en',
  'en-GB': 'en',
  'en-US': 'en',
  'en-IE': 'en',
  'en-AU': 'en',
  'en-CA': 'en',
  'en-NZ': 'en',

  // German-speaking DACH
  'de': 'de',
  'de-DE': 'de',
  'de-AT': 'de',
  'de-CH': 'de',

  // French-speaking markets
  'fr': 'fr',
  'fr-FR': 'fr',
  'fr-BE': 'fr',
  'fr-CH': 'fr',
  'fr-CA': 'fr',
  'fr-LU': 'fr',

  // Italian-speaking markets
  'it': 'it',
  'it-IT': 'it',
  'it-CH': 'it',
  'it-SM': 'it',

  // Spanish-speaking markets (Iberia + core LatAm)
  'es': 'es',
  'es-ES': 'es',
  'es-MX': 'es',
  'es-AR': 'es',
  'es-CL': 'es',
  'es-CO': 'es',
  'es-PE': 'es',
  'es-US': 'es',
};
