import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { JsonLd } from '@/components/JsonLd';
import {
  absoluteUrl,
  buildMetadata,
  localizedPath,
  SITE_NAME,
} from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import { fetchLeaguesServer } from '@/lib/server-api';
import { type Locale } from '@/lib/i18n';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type PageProps = {
  params: { locale: Locale; league: string; match: string };
};

type MatchWrapper = {
  slug: string;
  league: string;
  league_name: string;
  home_team: string;
  away_team: string;
  kickoff: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  pick: string;
  prose: string;
  is_archived?: boolean;
  actual_result?: 'H' | 'D' | 'A' | null;
  actual_score?: string | null;
  pick_correct?: boolean | null;
};

async function fetchMatchWrapper(slug: string): Promise<MatchWrapper | null> {
  try {
    const res = await fetch(
      `${API_URL}/seo/matches/${encodeURIComponent(slug)}`,
      { next: { revalidate: 600 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as MatchWrapper;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const wrapper = await fetchMatchWrapper(params.match);
  const path = `/leagues/${params.league.toUpperCase()}/${params.match}`;
  if (!wrapper) {
    // Per Battle Plan §4: noindex if no genuine 150+ word wrapper exists.
    return {
      ...buildMetadata({
        title: `${params.match} · Match`,
        description: 'Match preview not yet available.',
        path,
        locale: params.locale,
      }),
      robots: { index: false, follow: true },
    };
  }
  return buildMetadata({
    title: `${wrapper.home_team} vs ${wrapper.away_team} · Prediction & odds`,
    description: wrapper.prose.slice(0, 160),
    path,
    locale: params.locale,
    ogType: 'article',
  });
}

export default async function MatchPredictionPage({ params }: PageProps) {
  const wrapper = await fetchMatchWrapper(params.match);
  const { locale } = getServerDictionary(params.locale);
  const leagues = await fetchLeaguesServer();
  const leagueKey = params.league.toUpperCase();
  const league = leagues.find((l) => l.key === leagueKey);
  if (!league && leagues.length > 0) {
    notFound();
  }
  const leagueName = league?.name ?? leagueKey;

  if (!wrapper) {
    // Render a minimal placeholder (already noindex via metadata).
    return (
      <article className="prose-editorial mx-auto max-w-3xl">
        <h1 className="text-2xl font-medium text-text">Match preview</h1>
        <p className="text-muted">
          A detailed preview for this match has not been published yet. Please
          check back closer to kick-off.
        </p>
      </article>
    );
  }

  const url = absoluteUrl(
    localizedPath(locale, `/leagues/${leagueKey}/${wrapper.slug}`),
  );

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: absoluteUrl(localizedPath(locale, '/')) },
      { '@type': 'ListItem', position: 2, name: 'Leagues', item: absoluteUrl(localizedPath(locale, '/leagues')) },
      {
        '@type': 'ListItem',
        position: 3,
        name: leagueName,
        item: absoluteUrl(localizedPath(locale, `/leagues/${leagueKey}`)),
      },
      {
        '@type': 'ListItem',
        position: 4,
        name: `${wrapper.home_team} vs ${wrapper.away_team}`,
        item: url,
      },
    ],
  };

  const sportsEventLd = {
    '@type': 'SportsEvent',
    name: `${wrapper.home_team} vs ${wrapper.away_team}`,
    startDate: wrapper.kickoff,
    sport: 'Association football',
    homeTeam: { '@type': 'SportsTeam', name: wrapper.home_team },
    awayTeam: { '@type': 'SportsTeam', name: wrapper.away_team },
    additionalProperty: [
      { '@type': 'PropertyValue', name: 'prob_home', value: wrapper.prob_home },
      { '@type': 'PropertyValue', name: 'prob_draw', value: wrapper.prob_draw },
      { '@type': 'PropertyValue', name: 'prob_away', value: wrapper.prob_away },
    ],
  };

  const articleLd = {
    '@context': 'https://schema.org',
    '@type': 'AnalysisNewsArticle',
    headline: `${wrapper.home_team} vs ${wrapper.away_team} · Prediction`,
    description: wrapper.prose.slice(0, 200),
    url,
    inLanguage: locale,
    isPartOf: { '@type': 'WebSite', name: SITE_NAME, url: absoluteUrl('/') },
    datePublished: wrapper.kickoff,
    dateModified: wrapper.kickoff,
    author: { '@type': 'Organization', name: SITE_NAME },
    publisher: { '@type': 'Organization', name: SITE_NAME },
    mainEntityOfPage: url,
    about: sportsEventLd,
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, articleLd]} />
      <article className="prose-editorial mx-auto max-w-3xl">
        <header className="mb-6 border-b border-white/10 pb-6">
          <p className="text-2xs uppercase tracking-[0.08em] text-muted">
            {leagueName}
          </p>
          <h1 className="mt-2 text-2xl font-medium text-text">
            {wrapper.home_team} vs {wrapper.away_team}
          </h1>
          <dl className="mt-3 text-2xs uppercase tracking-[0.08em] text-muted">
            <dt className="sr-only">Kick-off</dt>
            <dd>
              <time dateTime={wrapper.kickoff}>{wrapper.kickoff}</time>
            </dd>
          </dl>
        </header>

        <section className="grid grid-cols-3 gap-3 text-center">
          <div className="surface-card px-3 py-3">
            <p className="text-2xs uppercase text-muted">Home</p>
            <p className="mt-1 font-mono text-lg text-text">
              {Math.round(wrapper.prob_home * 100)}%
            </p>
          </div>
          <div className="surface-card px-3 py-3">
            <p className="text-2xs uppercase text-muted">Draw</p>
            <p className="mt-1 font-mono text-lg text-text">
              {Math.round(wrapper.prob_draw * 100)}%
            </p>
          </div>
          <div className="surface-card px-3 py-3">
            <p className="text-2xs uppercase text-muted">Away</p>
            <p className="mt-1 font-mono text-lg text-text">
              {Math.round(wrapper.prob_away * 100)}%
            </p>
          </div>
        </section>

        <section className="mt-6 space-y-4 text-sm leading-relaxed text-text">
          {wrapper.prose.split('\n\n').map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </section>

        {wrapper.is_archived && wrapper.actual_result && (
          <section className="mt-8 rounded-md border border-white/10 bg-white/5 p-4">
            <p className="text-2xs uppercase tracking-[0.08em] text-muted">
              Result
            </p>
            <p className="mt-2 font-mono text-text">
              {wrapper.actual_score ?? wrapper.actual_result} ·{' '}
              {wrapper.pick_correct ? '✓ Pick correct' : '✗ Pick incorrect'}
            </p>
          </section>
        )}
      </article>
    </>
  );
}
