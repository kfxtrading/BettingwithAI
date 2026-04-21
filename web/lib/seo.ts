import type { Metadata } from 'next';
import {
  defaultLocale,
  hreflangRegions,
  locales,
  ogLocaleMap,
  type Locale,
} from './i18n';

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export const SITE_NAME = 'Betting with AI';

/**
 * Strip a leading locale segment (e.g. "/en/leagues" -> "/leagues").
 * Returns the path unchanged when it does not start with a known locale.
 */
export function stripLocale(path: string): string {
  const m = path.match(/^\/([a-z]{2})(?=\/|$)/i);
  if (m && (locales as readonly string[]).includes(m[1].toLowerCase())) {
    const rest = path.slice(m[0].length);
    return rest.length === 0 ? '/' : rest;
  }
  return path.startsWith('/') ? path : `/${path}`;
}

/**
 * Build a locale-prefixed path. `path` should be locale-agnostic
 * (e.g. "/", "/leagues", "/leagues/PL"). The locale is always
 * prepended, so `/` becomes `/en` and `/leagues` becomes `/en/leagues`.
 */
export function localizedPath(locale: Locale, path = '/'): string {
  const cleaned = stripLocale(path);
  if (cleaned === '/') return `/${locale}`;
  return `/${locale}${cleaned}`;
}

export function absoluteUrl(path = '/'): string {
  const base = SITE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * Build hreflang alternates for a locale-agnostic path.
 * Each entry maps a BCP-47 tag to the absolute URL of the
 * matching localized variant. Includes `x-default` -> default locale.
 */
export function buildLanguageAlternates(
  path = '/',
): Record<string, string> {
  const alternates: Record<string, string> = {};
  for (const [tag, locale] of Object.entries(hreflangRegions)) {
    alternates[tag] = absoluteUrl(localizedPath(locale, path));
  }
  alternates['x-default'] = absoluteUrl(localizedPath(defaultLocale, path));
  return alternates;
}

type BuildMetadataInput = {
  title: string;
  description: string;
  /** Locale-agnostic path (without `/en`, `/de` etc. prefix). */
  path?: string;
  locale?: Locale;
  keywords?: string[];
  ogType?: 'website' | 'article';
  /** When true, emit `noindex, follow` robots directives. */
  noIndex?: boolean;
};

export function buildMetadata({
  title,
  description,
  path = '/',
  locale = defaultLocale,
  keywords,
  ogType = 'website',
  noIndex = false,
}: BuildMetadataInput): Metadata {
  const canonicalPath = localizedPath(locale, path);
  const url = absoluteUrl(canonicalPath);
  return {
    title,
    description,
    keywords,
    robots: noIndex
      ? {
          index: false,
          follow: true,
          googleBot: { index: false, follow: true },
        }
      : undefined,
    alternates: {
      canonical: url,
      languages: buildLanguageAlternates(path),
    },
    openGraph: {
      type: ogType,
      url,
      title,
      description,
      siteName: SITE_NAME,
      locale: ogLocaleMap[locale],
      alternateLocale: locales
        .filter((l) => l !== locale)
        .map((l) => ogLocaleMap[l]),
      images: [
        { url: absoluteUrl('/og.png'), width: 1200, height: 630, alt: SITE_NAME },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [absoluteUrl('/og.png')],
    },
  };
}
