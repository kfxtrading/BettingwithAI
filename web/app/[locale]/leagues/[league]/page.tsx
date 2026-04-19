import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { LeagueClient } from '@/app/leagues/[league]/LeagueClient';
import { JsonLd } from '@/components/JsonLd';
import {
  buildMetadata,
  SITE_NAME,
  absoluteUrl,
  localizedPath,
} from '@/lib/seo';
import { fetchLeaguesServer } from '@/lib/server-api';
import { locales, type Locale } from '@/lib/i18n';

type PageProps = {
  params: { locale: Locale; league: string };
};

export async function generateStaticParams(): Promise<
  { locale: Locale; league: string }[]
> {
  const leagues = await fetchLeaguesServer();
  const params: { locale: Locale; league: string }[] = [];
  for (const locale of locales) {
    for (const l of leagues) {
      params.push({ locale, league: l.key });
    }
  }
  return params;
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
    locale: params.locale,
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
      {
        '@type': 'ListItem',
        position: 3,
        name,
        item: absoluteUrl(localizedPath(locale, `/leagues/${leagueKey}`)),
      },
    ],
  };

  const sportsLeagueLd = {
    '@context': 'https://schema.org',
    '@type': 'SportsOrganization',
    name,
    sport: 'Association football',
    url: absoluteUrl(localizedPath(locale, `/leagues/${leagueKey}`)),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, sportsLeagueLd]} />
      <LeagueClient leagueKey={leagueKey} leagueName={name} />
    </>
  );
}
