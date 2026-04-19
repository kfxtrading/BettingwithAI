import type { Metadata } from 'next';
import { LeaguesClient } from '@/app/leagues/LeaguesClient';
import { JsonLd } from '@/components/JsonLd';
import {
  buildMetadata,
  SITE_NAME,
  absoluteUrl,
  localizedPath,
} from '@/lib/seo';
import { fetchLeaguesServer } from '@/lib/server-api';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['leagues.heading'],
    description: dict['leagues.description'],
    path: '/leagues',
    locale,
  });
}

export default async function LeaguesPage({ params }: PageProps) {
  const leagues = await fetchLeaguesServer();
  const locale = params.locale;

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: absoluteUrl(localizedPath(locale, '/')),
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Leagues',
        item: absoluteUrl(localizedPath(locale, '/leagues')),
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
      url: absoluteUrl(localizedPath(locale, `/leagues/${l.key}`)),
    })),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, itemListLd]} />
      <LeaguesClient />
    </>
  );
}
