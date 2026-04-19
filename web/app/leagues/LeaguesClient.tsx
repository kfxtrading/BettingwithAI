'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';

export function LeaguesClient() {
  const summariesQuery = useQuery({
    queryKey: queryKeys.leagueSummaries,
    queryFn: api.leagueSummaries,
  });

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.12em] text-muted">
          Leagues
        </p>
        <h1 className="max-w-3xl text-2xl font-medium tracking-tight">
          Pi-Ratings and form across every top league.
        </h1>
      </header>

      <Section>
        {summariesQuery.isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {summariesQuery.data?.map((league) => (
              <Link
                key={league.league}
                href={`/leagues/${league.league}`}
                className="surface-card focus-ring press flex flex-col gap-4 px-5 py-5 transition-[transform,box-shadow] ease-ease hover:-translate-y-[1px]"
              >
                <header className="flex items-baseline justify-between text-2xs">
                  <span className="pill">{league.league}</span>
                  <span className="font-mono text-muted">
                    {league.n_teams} teams
                  </span>
                </header>
                <div>
                  <h3 className="text-base font-medium tracking-tight">
                    {league.league_name}
                  </h3>
                  {league.leader ? (
                    <p className="mt-2 text-sm text-muted">
                      Leader:{' '}
                      <span className="text-text">{league.leader}</span>{' '}
                      <span className="font-mono">
                        ({league.leader_rating?.toFixed(3)})
                      </span>
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-muted">
                      No data yet — run `fb download`.
                    </p>
                  )}
                </div>
                <span className="mt-auto text-2xs text-accent">
                  View details →
                </span>
              </Link>
            ))}
          </div>
        )}
      </Section>
    </>
  );
}
