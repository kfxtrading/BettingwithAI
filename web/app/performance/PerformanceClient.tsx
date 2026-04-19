'use client';

import { useQuery } from '@tanstack/react-query';
import { BankrollChart } from '@/components/BankrollChart';
import { KpiTile } from '@/components/KpiTile';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function PerformanceClient() {
  const summaryQuery = useQuery({
    queryKey: queryKeys.performance,
    queryFn: api.performance,
  });
  const bankrollQuery = useQuery({
    queryKey: queryKeys.bankroll,
    queryFn: api.bankroll,
  });

  const s = summaryQuery.data;
  const tone = (value: number): 'positive' | 'negative' | 'default' =>
    value > 0 ? 'positive' : value < 0 ? 'negative' : 'default';

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.12em] text-muted">
          Model transparency
        </p>
        <h1 className="max-w-3xl text-2xl font-medium tracking-tight">
          Performance across the entire betting history.
        </h1>
      </header>

      <Section title="Core Metrics">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <KpiTile
            label="Bets"
            value={s?.n_bets ?? '—'}
            hint={s ? `${s.n_predictions} predictions total` : undefined}
          />
          <KpiTile
            label="Hit Rate"
            value={s ? pct(s.hit_rate) : '—'}
          />
          <KpiTile
            label="ROI"
            value={s ? pct(s.roi, 2) : '—'}
            tone={s ? tone(s.roi) : 'default'}
          />
          <KpiTile
            label="Max Drawdown"
            value={s ? `${s.max_drawdown_pct.toFixed(1)}%` : '—'}
            tone="negative"
          />
        </div>
      </Section>

      <Section title="Bankroll Curve" caption="Starting bankroll 1,000.">
        {bankrollQuery.isLoading ? (
          <div className="h-72 animate-pulse rounded-[14px] bg-surface-2" />
        ) : (
          <BankrollChart data={bankrollQuery.data ?? []} />
        )}
      </Section>

      <Section title="Breakdown by League">
        {!s || s.per_league.length === 0 ? (
          <div className="surface-card px-5 py-12 text-center text-sm text-muted">
            No settled bets per league yet.
          </div>
        ) : (
          <div className="surface-card overflow-hidden">
            <div className="hidden grid-cols-[2.5rem_1fr_4rem_5rem_5rem] gap-4 px-5 py-3 text-2xs uppercase tracking-[0.08em] text-muted md:grid">
              <span>League</span>
              <span>Name</span>
              <span className="text-right">Bets</span>
              <span className="text-right">Hit Rate</span>
              <span className="text-right">ROI</span>
            </div>
            <ul>
              {s.per_league.map((row) => (
                <li
                  key={row.league}
                  className="hairline grid grid-cols-[2.5rem_1fr_4rem_5rem_5rem] items-center gap-4 px-5 py-3 text-sm first:border-none"
                >
                  <span className="font-mono text-muted">{row.league}</span>
                  <span className="truncate">{row.league_name}</span>
                  <span className="text-right font-mono">{row.n_bets}</span>
                  <span className="text-right font-mono">
                    {pct(row.hit_rate)}
                  </span>
                  <span
                    className={`text-right font-mono ${
                      row.roi > 0
                        ? 'text-positive'
                        : row.roi < 0
                          ? 'text-negative'
                          : ''
                    }`}
                  >
                    {pct(row.roi, 2)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>
    </>
  );
}
