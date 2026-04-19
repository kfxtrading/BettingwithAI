import type { Metadata } from 'next';
import {
  defaultLocale,
  hreflangRegions,
  ogLocaleMap,
  type Locale,
} from './i18n';

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export const SITE_NAME = 'Betting with AI';

export function absoluteUrl(path = '/'): string {
  const base = SITE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

export function buildLanguageAlternates(
  path = '/',
): Record<string, string> {
  const url = absoluteUrl(path);
  const alternates: Record<string, string> = {};
  for (const tag of Object.keys(hreflangRegions)) {
    alternates[tag] = url;
  }
  alternates['x-default'] = url;
  return alternates;
}

type BuildMetadataInput = {
  title: string;
  description: string;
  path?: string;
  locale?: Locale;
  keywords?: string[];
  ogType?: 'website' | 'article';
};

export function buildMetadata({
  title,
  description,
  path = '/',
  locale = defaultLocale,
  keywords,
  ogType = 'website',
}: BuildMetadataInput): Metadata {
  const url = absoluteUrl(path);
  return {
    title,
    description,
    keywords,
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
      images: [{ url: absoluteUrl('/og.png'), width: 1200, height: 630, alt: SITE_NAME }],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [absoluteUrl('/og.png')],
    },
  };
}
