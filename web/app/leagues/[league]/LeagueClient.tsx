'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Section } from '@/components/Section';
import { RatingsTable } from '@/components/RatingsTable';
import { Empty } from '@/components/Empty';
import { api, queryKeys } from '@/lib/api';
import type { FormRow } from '@/lib/types';

type Props = {
  leagueKey: string;
  leagueName: string;
};

export function LeagueClient({ leagueKey, leagueName }: Props) {
  const ratingsQuery = useQuery({
    queryKey: queryKeys.ratings(leagueKey, 24),
    queryFn: () => api.ratings(leagueKey, 24),
    enabled: leagueKey.length > 0,
  });
  const formQuery = useQuery({
    queryKey: queryKeys.form(leagueKey, 50),
    queryFn: () => api.form(leagueKey, 50),
    enabled: leagueKey.length > 0,
  });

  const formMap: Record<string, FormRow> = {};
  for (const row of formQuery.data ?? []) {
    formMap[row.team] = row;
  }

  return (
    <>
      <header className="flex flex-col gap-3">
        <Link
          href="/leagues"
          className="focus-ring text-2xs uppercase tracking-[0.12em] text-muted hover:text-text"
        >
          ← All leagues
        </Link>
        <h1 className="text-2xl font-medium tracking-tight">{leagueName}</h1>
        <p className="text-sm text-muted">
          Pi-Ratings after Constantinou &amp; Fenton (2013) — split by home and
          away strength.
        </p>
      </header>

      <Section title="Table">
        {ratingsQuery.isLoading ? (
          <div className="surface-card h-96 animate-pulse" />
        ) : ratingsQuery.isError || (ratingsQuery.data?.length ?? 0) === 0 ? (
          <Empty
            title="No data"
            hint="Load league data with `fb download --league all`."
          />
        ) : (
          <RatingsTable rows={ratingsQuery.data ?? []} forms={formMap} />
        )}
      </Section>
    </>
  );
}
