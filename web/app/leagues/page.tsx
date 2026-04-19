import type { Metadata } from 'next';
import { LeaguesClient } from './LeaguesClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, SITE_NAME, absoluteUrl } from '@/lib/seo';
import { fetchLeaguesServer } from '@/lib/server-api';
import { getServerDictionary } from '@/lib/i18n/server';

export function generateMetadata(): Metadata {
  const { locale, dict } = getServerDictionary();
  return buildMetadata({
    title: `${dict['leagues.heading']}`,
    description: dict['leagues.description'],
    path: '/leagues',
    locale,
  });
}

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
