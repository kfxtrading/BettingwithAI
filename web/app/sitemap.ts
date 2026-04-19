import type { MetadataRoute } from 'next';
import { absoluteUrl } from '@/lib/seo';

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

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const staticPaths: MetadataRoute.Sitemap = [
    {
      url: absoluteUrl('/'),
      lastModified: now,
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: absoluteUrl('/leagues'),
      lastModified: now,
      changeFrequency: 'daily',
      priority: 0.8,
    },
    {
      url: absoluteUrl('/performance'),
      lastModified: now,
      changeFrequency: 'daily',
      priority: 0.7,
    },
  ];

  const leagues = await fetchLeagues();
  const leaguePaths: MetadataRoute.Sitemap = leagues.map((l) => ({
    url: absoluteUrl(`/leagues/${l.key}`),
    lastModified: now,
    changeFrequency: 'daily',
    priority: 0.7,
  }));

  return [...staticPaths, ...leaguePaths];
}
