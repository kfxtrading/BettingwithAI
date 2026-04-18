'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { LeagueSwitcher } from '@/components/LeagueSwitcher';
import { PerformanceTracker } from '@/components/PerformanceTracker';
import { PredictionCard } from '@/components/PredictionCard';
import { Section } from '@/components/Section';
import { Empty } from '@/components/Empty';
import { ValueBetBadge } from '@/components/ValueBetBadge';
import { api, queryKeys } from '@/lib/api';

function formatGenerated(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en-GB', {
      dateStyle: 'long',
      timeStyle: 'short',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function HomePage() {
  const [league, setLeague] = useState<string | null>(null);

  const leaguesQuery = useQuery({
    queryKey: queryKeys.leagues,
    queryFn: api.leagues,
  });

  const todayQuery = useQuery({
    queryKey: queryKeys.today(league ?? undefined),
    queryFn: () => api.today(league ?? undefined),
  });

  const predictions = todayQuery.data?.predictions ?? [];
  const valueBets = todayQuery.data?.value_bets ?? [];

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.12em] text-muted">
          {todayQuery.data
            ? formatGenerated(todayQuery.data.generated_at)
            : 'Loading predictions…'}
        </p>
        <h1 className="max-w-3xl text-2xl font-medium tracking-tight">
          Today's betting analyses for the Top 5 leagues.
        </h1>
      </header>

      <Section
        title="Value Bets"
        caption="Discrepancies identified between model and market."
        action={
          leaguesQuery.data ? (
            <LeagueSwitcher
              leagues={leaguesQuery.data}
              value={league}
              onChange={setLeague}
            />
          ) : null
        }
      >
        {todayQuery.isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="h-44 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
        ) : valueBets.length === 0 ? (
          <Empty
            title="No value bets right now"
            hint="When the model finds a significant edge over the market, opportunities will appear here."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {valueBets.slice(0, 9).map((bet, i) => (
              <ValueBetBadge key={`${bet.home_team}-${i}`} bet={bet} />
            ))}
          </div>
        )}
      </Section>

      <Section
        title="Today's Predictions"
        caption="Probabilities for Home · Draw · Away."
      >
        {todayQuery.isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-48 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
        ) : predictions.length === 0 ? (
          <Empty
            title="No predictions available"
            hint='Generate a snapshot with `fb snapshot` or drop a fixtures file into "data/".'
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {predictions.map((p, i) => (
              <PredictionCard
                key={`${p.home_team}-${p.away_team}-${i}`}
                prediction={p}
              />
            ))}
          </div>
        )}
      </Section>

      <PerformanceTracker />
    </>
  );
}
