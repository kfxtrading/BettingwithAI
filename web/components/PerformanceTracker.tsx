'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { BankrollChart } from '@/components/BankrollChart';
import { KpiTile } from '@/components/KpiTile';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function PerformanceTracker() {
  const { t } = useLocale();
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
    <Section title={t('transparency.title')}>
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
          {t('transparency.updating')}
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiTile
              label={t('kpi.bets')}
              value={s.n_bets}
              hint={t('kpi.bets.hint', { n: s.n_predictions })}
            />
            <KpiTile
              label={t('kpi.hitRate')}
              value={s.n_bets > 0 ? pct(s.hit_rate) : '—'}
              hint={
                s.n_bets === 0 ? t('kpi.hitRate.noBets') : t('kpi.hitRate.hint')
              }
            />
            <KpiTile
              label={t('kpi.roi')}
              value={s.n_bets > 0 ? pct(s.roi, 2) : '—'}
              tone={tone(s.roi)}
            />
            <KpiTile
              label={t('kpi.maxDrawdown')}
              value={`${s.max_drawdown_pct.toFixed(1)}%`}
              tone="negative"
            />
          </div>

          <BankrollChart data={bankroll} />

          <p className="text-2xs leading-relaxed text-muted">
            {t('transparency.disclaimer')}
          </p>

          <div className="flex justify-center pt-2">
            <Link
              href="/performance"
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
