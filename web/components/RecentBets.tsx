'use client';

import { useQuery } from '@tanstack/react-query';
import { Check, Clock, X } from 'lucide-react';
import { Empty } from '@/components/Empty';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';
import type { BetStatus, GradedBet, HistoryDay } from '@/lib/types';

const DAYS = 14;

function formatDay(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
    }).format(d);
  } catch {
    return iso;
  }
}

function StatusBadge({ status }: { status: BetStatus }) {
  const base =
    'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium uppercase tracking-[0.08em]';
  if (status === 'won') {
    return (
      <span className={`${base} bg-positive/15 text-positive`}>
        <Check size={12} /> Won
      </span>
    );
  }
  if (status === 'lost') {
    return (
      <span className={`${base} bg-negative/15 text-negative`}>
        <X size={12} /> Lost
      </span>
    );
  }
  return (
    <span className={`${base} bg-surface-2 text-muted`}>
      <Clock size={12} /> Pending
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

function BetRow({ bet }: { bet: GradedBet }) {
  return (
    <li className="grid grid-cols-[1fr_auto] items-center gap-3 border-t border-border/40 py-3 first:border-t-0">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">
          {bet.home_team} <span className="text-muted">vs</span> {bet.away_team}
        </p>
        <p className="mt-0.5 truncate text-2xs uppercase tracking-[0.08em] text-muted">
          {bet.league_name} · {bet.bet_label} @ {bet.odds.toFixed(2)}
          {bet.ft_score ? `  ·  ${bet.ft_score}` : ''}
        </p>
      </div>
      <div className="flex flex-col items-end gap-1">
        <StatusBadge status={bet.status} />
        {bet.status !== 'pending' && <Pnl value={bet.pnl} />}
      </div>
    </li>
  );
}

function DayBlock({ day }: { day: HistoryDay }) {
  return (
    <div className="surface-card px-5 py-4">
      <header className="mb-2 flex items-end justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{formatDay(day.date)}</p>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.08em] text-muted">
            {day.n_bets} {day.n_bets === 1 ? 'Bet' : 'Bets'}
            {day.n_won + day.n_lost > 0
              ? `  ·  ${day.n_won}W / ${day.n_lost}L`
              : ''}
            {day.n_pending > 0 ? `  ·  ${day.n_pending} pending` : ''}
          </p>
        </div>
        {day.n_won + day.n_lost > 0 && <Pnl value={day.pnl} />}
      </header>
      <ul>
        {day.bets.map((bet, i) => (
          <BetRow
            key={`${bet.home_team}-${bet.away_team}-${bet.outcome}-${i}`}
            bet={bet}
          />
        ))}
      </ul>
    </div>
  );
}

export function RecentBets() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.history(DAYS),
    queryFn: () => api.history(DAYS),
    staleTime: 60_000,
  });

  const caption = data
    ? `Last ${data.n_days} ${data.n_days === 1 ? 'day' : 'days'} · ${data.total_bets} bets · Hit rate ${
        data.hit_rate != null ? `${(data.hit_rate * 100).toFixed(1)}%` : '—'
      }`
    : 'Evaluation of past value bets';

  return (
    <Section title="Recent Bets" caption={caption}>
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
          History is being updated.
        </div>
      ) : data.days.length === 0 ? (
        <Empty
          title="No settled bets yet"
          hint="As soon as the first matches finish, results will appear here with green/red evaluation."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.days.map((day) => (
            <DayBlock key={day.date} day={day} />
          ))}
        </div>
      )}
    </Section>
  );
}
