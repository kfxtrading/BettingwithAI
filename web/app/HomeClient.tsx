'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { LeagueSwitcher } from '@/components/LeagueSwitcher';
import { PerformanceTracker } from '@/components/PerformanceTracker';
import { PredictionCard } from '@/components/PredictionCard';
import { RecentBets } from '@/components/RecentBets';
import { Section } from '@/components/Section';
import { Empty } from '@/components/Empty';
import { ValueBetBadge } from '@/components/ValueBetBadge';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import type { League, TodayPayload } from '@/lib/types';

type HomeClientProps = {
  initialToday?: TodayPayload | null;
  initialLeagues?: League[];
};

function formatGenerated(iso: string, locale: string): string {
  try {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'long',
      timeStyle: 'short',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function HomeClient({
  initialToday,
  initialLeagues,
}: HomeClientProps = {}) {
  const [league, setLeague] = useState<string | null>(null);
  const { t, locale } = useLocale();

  const leaguesQuery = useQuery({
    queryKey: queryKeys.leagues,
    queryFn: api.leagues,
    initialData: initialLeagues,
  });

  const todayQuery = useQuery({
    queryKey: queryKeys.today(league ?? undefined),
    queryFn: () => api.today(league ?? undefined),
    initialData: league === null ? initialToday ?? undefined : undefined,
  });

  const predictions = todayQuery.data?.predictions ?? [];
  const valueBets = todayQuery.data?.value_bets ?? [];

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.12em] text-muted">
          {todayQuery.data
            ? formatGenerated(todayQuery.data.generated_at, locale)
            : t('home.loading')}
        </p>
        <h1 className="max-w-3xl text-2xl font-medium tracking-tight">
          {t('home.heading')}
        </h1>
      </header>

      <Section
        title={t('home.section.valueBets.title')}
        caption={t('home.section.valueBets.caption')}
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
            title={t('home.section.valueBets.empty.title')}
            hint={t('home.section.valueBets.empty.hint')}
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
        title={t('home.section.predictions.title')}
        caption={t('home.section.predictions.caption')}
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
            title={t('home.section.predictions.empty.title')}
            hint={t('home.section.predictions.empty.hint')}
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

      <RecentBets />
    </>
  );
}
