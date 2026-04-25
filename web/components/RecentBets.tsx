'use client';

import { useQuery } from '@tanstack/react-query';
import { Clock } from 'lucide-react';
import { Empty } from '@/components/Empty';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';
import type { BetStatus, GradedBet, HistoryDay } from '@/lib/types';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import type { DictionaryKey } from '@/lib/i18n';
import { parseLocalDate } from '@/lib/datetime';

const DAYS = 14;
const MAX_VISIBLE_DAYS = 6;

function formatDay(iso: string, locale: string): string {
  try {
    // ``new Date("YYYY-MM-DD")`` is UTC midnight, which shifts the day for
    // users west of UTC. Parse as a local calendar day instead.
    const d = parseLocalDate(iso) ?? new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(locale, {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
    }).format(d);
  } catch {
    return iso;
  }
}

function StatusBadge({
  status,
  t,
}: {
  status: BetStatus;
  t: (key: DictionaryKey) => string;
}) {
  if (status !== 'pending') {
    return null;
  }
  const base =
    'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium uppercase tracking-[0.08em]';
  return (
    <span className={`${base} bg-surface-2 text-muted`}>
      <Clock size={12} /> {t('recentBets.status.pending')}
    </span>
  );
}

function Pnl({ value }: { value: number }) {
  if (value === 0) return <span className="font-mono text-sm text-muted">±0.00</span>;
  const cls = value > 0 ? 'text-positive' : 'text-negative';
  const sign = value > 0 ? '+' : '';
  return (
    <span className={`font-mono text-sm ${cls}`}>
      {sign}
      {value.toFixed(2)}
    </span>
  );
}

function matchKey(bet: GradedBet): string {
  return `${bet.date}|${bet.league}|${bet.home_team}|${bet.away_team}`;
}

function groupByMatch(bets: GradedBet[]): GradedBet[][] {
  const groups = new Map<string, GradedBet[]>();
  for (const bet of bets) {
    const key = matchKey(bet);
    const existing = groups.get(key);
    if (existing) {
      existing.push(bet);
    } else {
      groups.set(key, [bet]);
    }
  }
  return Array.from(groups.values());
}

function MatchRow({
  bets,
  t,
}: {
  bets: GradedBet[];
  t: (key: DictionaryKey) => string;
}) {
  const first = bets[0];
  const combinedPnl = bets.reduce((sum, b) => sum + b.pnl, 0);
  const hasSettled = bets.some((b) => b.status !== 'pending');
  const groupStatus: BetStatus = bets.some((b) => b.status === 'won')
    ? 'won'
    : bets.every((b) => b.status === 'lost')
      ? 'lost'
      : bets.some((b) => b.status === 'pending')
        ? 'pending'
        : 'lost';

  return (
    <li className="grid grid-cols-[1fr_auto] items-center gap-3 border-t border-border/40 py-3 first:border-t-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">
          {first.home_team} <span className="text-muted">vs</span> {first.away_team}
        </p>
        <p className="mt-0.5 truncate text-2xs uppercase tracking-[0.08em] text-muted">
          {first.league_name}
          {first.ft_score ? `  ·  ${first.ft_score}` : ''}
        </p>
        <ul className="mt-1 space-y-0.5">
          {bets.map((bet, i) => {
            const isPrediction = bet.kind === 'prediction';
            return (
              <li
                key={`${bet.outcome}-${bet.bet_label}-${i}`}
                className="truncate text-2xs text-muted"
              >
                <span
                  className={`mr-1.5 rounded-sm px-1 py-[1px] text-[9px] font-semibold uppercase tracking-wider ${
                    isPrediction
                      ? 'bg-surface-2 text-muted'
                      : 'bg-accent/15 text-accent'
                  }`}
                >
                  {isPrediction
                    ? t('recentBets.kind.prediction')
                    : t('recentBets.kind.value')}
                </span>
                <span className="uppercase tracking-[0.08em]">
                  {bet.bet_label} @ {bet.odds.toFixed(2)}
                </span>
                {bet.status !== 'pending' && (
                  <span
                    className={`ml-2 font-mono ${
                      bet.status === 'won' ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {bet.pnl > 0 ? '+' : ''}
                    {bet.pnl.toFixed(2)}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      </div>
      <div className="flex flex-col items-end gap-1">
        <StatusBadge status={groupStatus} t={t} />
        {hasSettled && <Pnl value={Math.round(combinedPnl * 100) / 100} />}
      </div>
    </li>
  );
}

function DayBlock({
  day,
  t,
  locale,
}: {
  day: HistoryDay;
  t: (key: DictionaryKey, vars?: Record<string, string | number>) => string;
  locale: string;
}) {
  const betsLabel = day.n_bets === 1 ? t('recentBets.day.bet') : t('recentBets.day.bets');
  return (
    <div className="surface-card px-5 py-4">
      <header className="mb-2 flex items-end justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{formatDay(day.date, locale)}</p>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.08em] text-muted">
            {day.n_bets} {betsLabel}
            {day.n_won + day.n_lost > 0
              ? `  ·  ${day.n_won}W / ${day.n_lost}L`
              : ''}
            {day.n_pending > 0
              ? `  ·  ${t('recentBets.day.pending', { n: day.n_pending })}`
              : ''}
          </p>
        </div>
        {day.n_won + day.n_lost > 0 && <Pnl value={day.pnl} />}
      </header>
      <ul>
        {groupByMatch(day.bets).map((bets) => (
          <MatchRow key={matchKey(bets[0])} bets={bets} t={t} />
        ))}
      </ul>
    </div>
  );
}

export function RecentBets() {
  const { t, locale } = useLocale();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.history(DAYS),
    queryFn: () => api.history(DAYS),
    staleTime: 60_000,
  });

  const caption = data
    ? t('recentBets.captionTemplate', {
        n: data.n_days,
        dayLabel:
          data.n_days === 1 ? t('recentBets.day.day') : t('recentBets.day.days'),
        bets: data.total_bets,
        rate:
          data.hit_rate != null ? `${(data.hit_rate * 100).toFixed(1)}%` : '—',
      })
    : t('recentBets.captionFallback');

  return (
    <Section title={t('recentBets.title')} caption={caption}>
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[0, 1].map((i) => (
            <div
              key={i}
              className="h-40 animate-pulse rounded-[14px] bg-surface-2"
            />
          ))}
        </div>
      ) : isError || !data ? (
        <div className="surface-card px-5 py-12 text-center text-sm text-muted">
          {t('recentBets.updating')}
        </div>
      ) : data.days.length === 0 ? (
        <Empty
          title={t('recentBets.empty.title')}
          hint={t('recentBets.empty.hint')}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.days.slice(0, MAX_VISIBLE_DAYS).map((day) => (
            <DayBlock key={day.date} day={day} t={t} locale={locale} />
          ))}
        </div>
      )}
    </Section>
  );
}
