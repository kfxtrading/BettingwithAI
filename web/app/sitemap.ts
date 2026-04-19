import type { MetadataRoute } from 'next';
import { absoluteUrl, buildLanguageAlternates, localizedPath } from '@/lib/seo';
import { defaultLocale, locales } from '@/lib/i18n';
import { LEARN_SLUGS } from '@/content/learn';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type LeagueOut = { key: string; name: string };

async function fetchLeagues(): Promise<LeagueOut[]> {
  try {
    const res = await fetch(`${API_URL}/leagues`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    return (await res.json()) as LeagueOut[];
  } catch {
    return [];
  }
}

type StaticEntry = {
  path: string;
  changeFrequency: MetadataRoute.Sitemap[number]['changeFrequency'];
  priority: number;
};

const STATIC_ROUTES: StaticEntry[] = [
  { path: '/', changeFrequency: 'daily', priority: 1.0 },
  { path: '/leagues', changeFrequency: 'daily', priority: 0.8 },
  { path: '/performance', changeFrequency: 'daily', priority: 0.7 },
  { path: '/track-record', changeFrequency: 'daily', priority: 0.8 },
  { path: '/learn', changeFrequency: 'weekly', priority: 0.7 },
  { path: '/about', changeFrequency: 'monthly', priority: 0.5 },
  { path: '/methodology', changeFrequency: 'monthly', priority: 0.6 },
  { path: '/responsible-gambling', changeFrequency: 'yearly', priority: 0.4 },
  { path: '/legal/terms', changeFrequency: 'yearly', priority: 0.3 },
  { path: '/legal/privacy', changeFrequency: 'yearly', priority: 0.3 },
  { path: '/legal/cookies', changeFrequency: 'yearly', priority: 0.3 },
];

const DE_ONLY_ROUTES: StaticEntry[] = [
  { path: '/impressum', changeFrequency: 'yearly', priority: 0.3 },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const leagues = await fetchLeagues();

  const entries: MetadataRoute.Sitemap = [];

  for (const route of STATIC_ROUTES) {
    for (const locale of locales) {
      entries.push({
        url: absoluteUrl(localizedPath(locale, route.path)),
        lastModified: now,
        changeFrequency: route.changeFrequency,
        priority: locale === defaultLocale ? route.priority : route.priority * 0.9,
        alternates: { languages: buildLanguageAlternates(route.path) },
      });
    }
  }

  for (const route of DE_ONLY_ROUTES) {
    entries.push({
      url: absoluteUrl(localizedPath('de', route.path)),
      lastModified: now,
      changeFrequency: route.changeFrequency,
      priority: route.priority,
    });
  }

  for (const l of leagues) {
    const path = `/leagues/${l.key}`;
    for (const locale of locales) {
      entries.push({
        url: absoluteUrl(localizedPath(locale, path)),
        lastModified: now,
        changeFrequency: 'daily',
        priority: locale === defaultLocale ? 0.7 : 0.6,
        alternates: { languages: buildLanguageAlternates(path) },
      });
    }
  }

  for (const slug of LEARN_SLUGS) {
    const path = `/learn/${slug}`;
    for (const locale of locales) {
      entries.push({
        url: absoluteUrl(localizedPath(locale, path)),
        lastModified: now,
        changeFrequency: 'monthly',
        priority: locale === defaultLocale ? 0.6 : 0.5,
        alternates: { languages: buildLanguageAlternates(path) },
      });
    }
  }

  return entries;
}
