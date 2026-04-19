import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { LeagueClient } from './LeagueClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, SITE_NAME, absoluteUrl } from '@/lib/seo';
import { fetchLeaguesServer } from '@/lib/server-api';

type PageProps = {
  params: { league: string };
};

export async function generateStaticParams(): Promise<{ league: string }[]> {
  const leagues = await fetchLeaguesServer();
  return leagues.map((l) => ({ league: l.key }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const leagueKey = (params.league ?? '').toUpperCase();
  const leagues = await fetchLeaguesServer();
  const league = leagues.find((l) => l.key === leagueKey);
  const name = league?.name ?? leagueKey;

  return buildMetadata({
    title: `${name} · Pi-Ratings, Form & Predictions`,
    description: `${name} Pi-Ratings, recent form, head-to-head data and AI-driven match predictions from the ${SITE_NAME} ensemble model.`,
    path: `/leagues/${leagueKey}`,
    keywords: [
      `${name} predictions`,
      `${name} Pi-Ratings`,
      `${name} value bets`,
      `${name} form table`,
    ],
  });
}

export default async function LeagueDetailPage({ params }: PageProps) {
  const leagueKey = (params.league ?? '').toUpperCase();
  const leagues = await fetchLeaguesServer();
  const league = leagues.find((l) => l.key === leagueKey);
  if (leagues.length > 0 && !league) {
    notFound();
  }
  const name = league?.name ?? leagueKey;

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: absoluteUrl('/') },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Leagues',
        item: absoluteUrl('/leagues'),
      },
      {
        '@type': 'ListItem',
        position: 3,
        name,
        item: absoluteUrl(`/leagues/${leagueKey}`),
      },
    ],
  };

  const sportsLeagueLd = {
    '@context': 'https://schema.org',
    '@type': 'SportsOrganization',
    name,
    sport: 'Association football',
    url: absoluteUrl(`/leagues/${leagueKey}`),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, sportsLeagueLd]} />
      <LeagueClient leagueKey={leagueKey} leagueName={name} />
    </>
  );
}
