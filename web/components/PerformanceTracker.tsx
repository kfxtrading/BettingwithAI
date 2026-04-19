'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { BankrollChart } from '@/components/BankrollChart';
import { KpiTile } from '@/components/KpiTile';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function PerformanceTracker() {
  const summaryQuery = useQuery({
    queryKey: queryKeys.performance,
    queryFn: api.performance,
    staleTime: 5 * 60_000,
  });
  const bankrollQuery = useQuery({
    queryKey: queryKeys.bankroll,
    queryFn: api.bankroll,
    staleTime: 5 * 60_000,
  });

  const isLoading = summaryQuery.isLoading || bankrollQuery.isLoading;
  const isError = summaryQuery.isError || bankrollQuery.isError;
  const s = summaryQuery.data;
  const bankroll = bankrollQuery.data ?? [];

  const tone = (v: number): 'positive' | 'negative' | 'default' =>
    v > 0 ? 'positive' : v < 0 ? 'negative' : 'default';

  return (
    <Section
      title="Transparency Tracker"
      caption="Bankroll curve · starting bankroll 1,000"
    >
      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
          <div className="h-80 animate-pulse rounded-[14px] bg-surface-2" />
        </div>
      ) : isError || !s ? (
        <div className="surface-card px-5 py-12 text-center text-sm text-muted">
          Performance data is being updated.
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiTile
              label="Bets"
              value={s.n_bets}
              hint={`${s.n_predictions} predictions total`}
            />
            <KpiTile
              label="Hit rate"
              value={s.n_bets > 0 ? pct(s.hit_rate) : '—'}
              hint={s.n_bets === 0 ? 'No settled bets yet' : 'Wins / settled bets'}
            />
            <KpiTile
              label="ROI"
              value={s.n_bets > 0 ? pct(s.roi, 2) : '—'}
              tone={tone(s.roi)}
            />
            <KpiTile
              label="Max drawdown"
              value={`${s.max_drawdown_pct.toFixed(1)}%`}
              tone="negative"
            />
          </div>

          <BankrollChart data={bankroll} />

          <p className="text-2xs leading-relaxed text-muted">
            Hypothetical simulation of a statistical model based on
            historical match data. Not a solicitation to gamble. No
            guarantee of future results. Gambling involves financial risk.
          </p>

          <div className="flex justify-center pt-2">
            <Link
              href="/performance"
              className="focus-ring press inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm font-medium text-white"
            >
              View full details
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      )}
    </Section>
  );
}
