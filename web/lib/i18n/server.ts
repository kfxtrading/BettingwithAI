import { cookies, headers } from 'next/headers';
import { defaultLocale, locales, type Locale } from './locales';
import { getDictionary, type Dictionary } from './index';

const LOCALE_COOKIE = 'NEXT_LOCALE';

export function isLocale(value: string | undefined | null): value is Locale {
  return !!value && (locales as readonly string[]).includes(value);
}

/**
 * Resolve the locale for the current server request.
 *
 * Preference order:
 *   1. Explicit `param` from a `[locale]` route segment.
 *   2. `NEXT_LOCALE` cookie.
 *   3. `Accept-Language` header.
 *   4. {@link defaultLocale}.
 */
export function getServerLocale(param?: string): Locale {
  if (isLocale(param)) return param;
  const headerStore = headers();
  const fromHeader = headerStore.get('x-locale');
  if (isLocale(fromHeader)) return fromHeader;
  const cookieStore = cookies();
  const fromCookie = cookieStore.get(LOCALE_COOKIE)?.value;
  if (isLocale(fromCookie)) return fromCookie;
  const accept = headerStore.get('accept-language');
  if (accept) {
    for (const part of accept.split(',')) {
      const tag = part.split(';')[0].trim().toLowerCase().slice(0, 2);
      if (isLocale(tag)) return tag;
    }
  }
  return defaultLocale;
}

export function getServerDictionary(
  param?: string,
): { locale: Locale; dict: Dictionary } {
  const locale = getServerLocale(param);
  return { locale, dict: getDictionary(locale) };
}
