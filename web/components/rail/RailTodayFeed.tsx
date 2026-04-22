'use client';

import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Clock, RefreshCcw } from 'lucide-react';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { useLanding } from '@/app/LandingContext';
import { formatKickoff } from '@/lib/datetime';
import type { Prediction } from '@/lib/types';

// Upper bound to keep the rail from growing unbounded on heavy match days.
// A single day rarely has more than ~20 fixtures across the leagues we cover.
const MAX_ITEMS = 20;

function matchKey(p: { date: string; home_team: string; away_team: string }): string {
  return `${p.date}|${p.home_team.toLowerCase().trim()}|${p.away_team.toLowerCase().trim()}`;
}

function pickUpcoming(
  predictions: Prediction[] | undefined,
  now: Date,
): Prediction[] {
  if (!predictions || predictions.length === 0) return [];
  const seen = new Set<string>();
  const enriched = predictions
    .map((p) => {
      const t = p.kickoff_utc ? Date.parse(p.kickoff_utc) : NaN;
      return { p, t };
    })
    .filter((x) => {
      // Hide matches that ended more than 105 min ago; keep entries without
      // a parseable kickoff_utc so at least the pairing is visible.
      if (Number.isFinite(x.t) && x.t < now.getTime() - 105 * 60_000) return false;
      const key = matchKey(x.p);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => {
      // Entries without kickoff_utc sort to the end but stay visible.
      const ta = Number.isFinite(a.t) ? a.t : Number.POSITIVE_INFINITY;
      const tb = Number.isFinite(b.t) ? b.t : Number.POSITIVE_INFINITY;
      return ta - tb;
    });
  return enriched.slice(0, MAX_ITEMS).map((x) => x.p);
}

function relativeMinutes(iso: string | null | undefined, now: Date): string {
  if (!iso) return '';
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return '';
  const diff = Math.round((t - now.getTime()) / 60_000);
  if (diff < -90) return '';
  if (diff < -1) return `${Math.abs(diff)}′`;
  if (diff < 1) return 'LIVE';
  if (diff < 60) return `${diff}m`;
  const h = Math.floor(diff / 60);
  const m = diff % 60;
  return m === 0 ? `${h}h` : `${h}h${m}m`;
}

function relativeSince(iso: string | undefined, now: Date): string | null {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  const diffSec = Math.max(0, Math.round((now.getTime() - t) / 1000));
  if (diffSec < 60) return `${diffSec}s`;
  const min = Math.floor(diffSec / 60);
  if (min < 60) return `${min}m`;
  const h = Math.floor(min / 60);
  return `${h}h${min % 60 ? ` ${min % 60}m` : ''}`;
}

export function RailTodayFeed() {
  const { t, locale } = useLocale();
  const { league } = useLanding();
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, []);

  const todayQuery = useQuery({
    queryKey: queryKeys.today(league ?? undefined),
    queryFn: () => api.today(league ?? undefined),
  });

  const effectiveNow = now ?? new Date(0);
  const upcoming = pickUpcoming(todayQuery.data?.predictions, effectiveNow);
  const snapshotAge = now
    ? relativeSince(todayQuery.data?.generated_at, now)
    : null;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between px-3 pt-1">
        <span className="text-2xs uppercase tracking-[0.12em] text-muted">
          {t('rail.section.today')}
        </span>
        {snapshotAge && (
          <span
            className="inline-flex items-center gap-1 text-2xs text-muted"
            suppressHydrationWarning
            title={t('rail.today.snapshot', { age: snapshotAge })}
          >
            <RefreshCcw size={10} strokeWidth={2} aria-hidden />
            {snapshotAge}
          </span>
        )}
      </div>

      {upcoming.length === 0 ? (
        <p className="px-3 py-2 text-xs text-muted">
          {t('rail.today.empty')}
        </p>
      ) : (
        <ul className="flex flex-col gap-0.5 px-1">
          {upcoming.map((p, idx) => {
            const rel = now ? relativeMinutes(p.kickoff_utc, now) : '';
            const time = formatKickoff(p.kickoff_utc, {
              locale,
              fallback: p.kickoff_time,
            });
            const live = p.is_live || rel === 'LIVE';
            return (
              <li
                key={`${p.home_team}-${p.away_team}-${idx}`}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs hover:bg-surface-2"
              >
                <span
                  className={`inline-flex w-12 shrink-0 items-center gap-1 font-mono text-[10px] tabular-nums ${
                    live ? 'text-negative' : 'text-muted'
                  }`}
                  suppressHydrationWarning
                >
                  {live ? (
                    <>
                      <span className="live-dot" aria-hidden />
                      <span>LIVE</span>
                    </>
                  ) : (
                    <>
                      <Clock
                        size={10}
                        strokeWidth={2}
                        aria-hidden
                        className="opacity-60"
                      />
                      <span>{rel || time}</span>
                    </>
                  )}
                </span>
                <span className="min-w-0 flex-1 truncate text-text">
                  <span className="text-text">{p.home_team}</span>
                  <span className="px-1 text-muted">·</span>
                  <span className="text-muted">{p.away_team}</span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
