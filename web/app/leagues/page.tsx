import type { Metadata } from 'next';
import { LeaguesClient } from './LeaguesClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, SITE_NAME, absoluteUrl } from '@/lib/seo';
import { fetchLeaguesServer } from '@/lib/server-api';

export const metadata: Metadata = buildMetadata({
  title: 'Football Leagues · Pi-Ratings, Form & Predictions',
  description:
    'Pi-Ratings, recent form and head-to-head data for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship — powered by the Betting with AI ensemble model.',
  path: '/leagues',
});

export default async function LeaguesPage() {
  const leagues = await fetchLeaguesServer();

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: absoluteUrl('/'),
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Leagues',
        item: absoluteUrl('/leagues'),
      },
    ],
  };

  const itemListLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${SITE_NAME} · Football Leagues`,
    itemListElement: leagues.map((l, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: l.name,
      url: absoluteUrl(`/leagues/${l.key}`),
    })),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, itemListLd]} />
      <LeaguesClient />
    </>
  );
}
