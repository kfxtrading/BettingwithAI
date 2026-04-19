import { cookies, headers } from 'next/headers';
import { defaultLocale, locales, type Locale } from './locales';
import { getDictionary, type Dictionary } from './index';

const LOCALE_COOKIE = 'NEXT_LOCALE';

export function getServerLocale(): Locale {
  const cookieStore = cookies();
  const fromCookie = cookieStore.get(LOCALE_COOKIE)?.value;
  if (fromCookie && (locales as readonly string[]).includes(fromCookie)) {
    return fromCookie as Locale;
  }
  const accept = headers().get('accept-language');
  if (accept) {
    for (const part of accept.split(',')) {
      const tag = part.split(';')[0].trim().toLowerCase().slice(0, 2);
      if ((locales as readonly string[]).includes(tag)) {
        return tag as Locale;
      }
    }
  }
  return defaultLocale;
}

export function getServerDictionary(): { locale: Locale; dict: Dictionary } {
  const locale = getServerLocale();
  return { locale, dict: getDictionary(locale) };
}
