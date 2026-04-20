'use client';

import { useQuery } from '@tanstack/react-query';
import { BankrollChart } from '@/components/BankrollChart';
import { KpiTile } from '@/components/KpiTile';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import type {
  BankrollPoint,
  PerformanceSummary,
  StrategyStats,
} from '@/lib/types';

type PerformanceClientProps = {
  initialSummary?: PerformanceSummary | null;
  initialBankroll?: BankrollPoint[];
};

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

function tone(value: number): 'positive' | 'negative' | 'default' {
  return value > 0 ? 'positive' : value < 0 ? 'negative' : 'default';
}

function StrategyGroup({
  title,
  stats,
  t,
}: {
  title: string;
  stats: StrategyStats | null;
  t: ReturnType<typeof useLocale>['t'];
}) {
  const hasData = !!stats && stats.n_bets > 0;
  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-2xs uppercase tracking-[0.12em] text-muted">
        {title}
      </h3>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiTile
          label={t('kpi.bets')}
          value={hasData ? stats!.n_bets : '—'}
        />
        <KpiTile
          label={t('kpi.hitRate')}
          value={hasData ? pct(stats!.hit_rate) : '—'}
        />
        <KpiTile
          label={t('kpi.roi')}
          value={hasData ? pct(stats!.roi, 2) : '—'}
          tone={hasData ? tone(stats!.roi) : 'default'}
        />
        <KpiTile
          label={t('kpi.maxDrawdown')}
          value={hasData ? `${stats!.max_drawdown_pct.toFixed(1)}%` : '—'}
          tone={hasData ? 'negative' : 'default'}
        />
      </div>
    </div>
  );
}

export function PerformanceClient({
  initialSummary,
  initialBankroll,
}: PerformanceClientProps = {}) {
  const { t } = useLocale();
  const summaryQuery = useQuery({
    queryKey: queryKeys.performance,
    queryFn: api.performance,
    initialData: initialSummary ?? undefined,
  });
  const bankrollQuery = useQuery({
    queryKey: queryKeys.bankroll,
    queryFn: api.bankroll,
    initialData: initialBankroll,
  });

  const s = summaryQuery.data;

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.12em] text-muted">
          {t('performance.label')}
        </p>
        <h1 className="max-w-3xl text-2xl font-medium tracking-tight">
          {t('performance.heading')}
        </h1>
      </header>

      <Section title={t('performance.section.coreMetrics')}>
        <div className="flex flex-col gap-6">
          <StrategyGroup
            title={t('transparency.group.valueBets')}
            stats={s?.value_bets ?? null}
            t={t}
          />
          <StrategyGroup
            title={t('transparency.group.predictions')}
            stats={s?.predictions ?? null}
            t={t}
          />
        </div>
      </Section>

      <Section
        title={t('performance.section.bankroll')}
        caption={t('performance.section.bankroll.caption')}
      >
        {bankrollQuery.isLoading ? (
          <div className="h-72 animate-pulse rounded-[14px] bg-surface-2" />
        ) : (
          <BankrollChart data={bankrollQuery.data ?? []} />
        )}
      </Section>

      <Section title={t('performance.section.byLeague')}>
        {!s || s.per_league.length === 0 ? (
          <div className="surface-card px-5 py-12 text-center text-sm text-muted">
            {t('performance.byLeague.empty')}
          </div>
        ) : (
          <div className="surface-card overflow-hidden">
            <div className="hidden grid-cols-[2.5rem_1fr_4rem_5rem_5rem] gap-4 px-5 py-3 text-2xs uppercase tracking-[0.08em] text-muted md:grid">
              <span>{t('performance.byLeague.col.league')}</span>
              <span>{t('performance.byLeague.col.name')}</span>
              <span className="text-right">
                {t('performance.byLeague.col.bets')}
              </span>
              <span className="text-right">
                {t('performance.byLeague.col.hitRate')}
              </span>
              <span className="text-right">
                {t('performance.byLeague.col.roi')}
              </span>
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
