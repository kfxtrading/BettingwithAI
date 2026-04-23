'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { BankrollChart } from '@/components/BankrollChart';
import { KpiTile } from '@/components/KpiTile';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import type { StrategyStats } from '@/lib/types';

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

function tone(v: number): 'positive' | 'negative' | 'default' {
  return v > 0 ? 'positive' : v < 0 ? 'negative' : 'default';
}

// The API merges the optimized-strategy baseline (internal 5-day backtest)
// with live post-cutoff graded bets server-side — see
// ``VALUE_SNAPSHOT_BASELINE`` / ``VALUE_SNAPSHOT_CUTOFF`` in
// ``api/services.py``. Pre-cutoff legacy rows are filtered out.
// The frontend therefore consumes ``summary.value_bets`` directly.

function StrategyKpiGroup({
  title,
  stats,
  labels,
  emptyHint,
}: {
  title: string;
  stats: StrategyStats | null | undefined;
  labels: {
    bets: string;
    hitRate: string;
    roi: string;
    drawdown: string;
  };
  emptyHint: string;
}) {
  const hasData = stats && stats.n_bets > 0;
  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-2xs uppercase tracking-[0.12em] text-muted">
        {title}
      </h3>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiTile
          label={labels.bets}
          value={hasData ? stats!.n_bets : '—'}
          hint={hasData ? undefined : emptyHint}
        />
        <KpiTile
          label={labels.hitRate}
          value={hasData ? pct(stats!.hit_rate) : '—'}
        />
        <KpiTile
          label={labels.roi}
          value={hasData ? pct(stats!.roi, 2) : '—'}
          tone={hasData ? tone(stats!.roi) : 'default'}
        />
        <KpiTile
          label={labels.drawdown}
          value={hasData ? `${stats!.max_drawdown_pct.toFixed(1)}%` : '—'}
          tone={hasData ? 'negative' : 'default'}
        />
      </div>
    </div>
  );
}

export function PerformanceTracker() {
  const { t, href } = useLocale();
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

  return (
    <Section title={t('transparency.title')}>
      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
          <div className="h-80 animate-pulse rounded-[14px] bg-surface-2" />
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <StrategyKpiGroup
            title={t('transparency.group.valueBets')}
            stats={s?.value_bets}
            labels={{
              bets: t('kpi.bets'),
              hitRate: t('kpi.hitRate'),
              roi: t('kpi.roi'),
              drawdown: t('kpi.maxDrawdown'),
            }}
            emptyHint={t('kpi.hitRate.noBets')}
          />
          <StrategyKpiGroup
            title={t('transparency.group.predictions')}
            stats={s?.predictions}
            labels={{
              bets: t('kpi.bets'),
              hitRate: t('kpi.hitRate'),
              roi: t('kpi.roi'),
              drawdown: t('kpi.maxDrawdown'),
            }}
            emptyHint={t('kpi.hitRate.noBets')}
          />

          <BankrollChart data={bankroll} />

          {isError || !s ? (
            <p className="text-2xs leading-relaxed text-muted">
              {t('transparency.updating')}
            </p>
          ) : null}

          <p className="text-2xs leading-relaxed text-muted">
            {t('transparency.disclaimer')}
          </p>

          <div className="flex justify-center pt-2">
            <Link
              href={href('/performance')}
              className="focus-ring press inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm font-medium text-white"
            >
              {t('transparency.viewFullDetails')}
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      )}
    </Section>
  );
}
