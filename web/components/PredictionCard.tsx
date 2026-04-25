'use client';

import { useEffect, useState } from 'react';
import { formatKickoff } from '@/lib/datetime';
import type { Prediction } from '@/lib/types';
import { ProbabilityBar } from './ProbabilityBar';
import { useLocale } from '@/lib/i18n/LocaleProvider';

function formatDate(iso: string, locale: string): string {
  const date = new Date(iso + 'T00:00:00');
  return new Intl.DateTimeFormat(locale, {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  }).format(date);
}

export function PredictionCard({ prediction }: { prediction: Prediction }) {
  const { t, locale } = useLocale();
  const { home_team, away_team, league_name, kickoff_time, odds } = prediction;
  const [viewerTimeZone, setViewerTimeZone] = useState<string | null>(null);

  useEffect(() => {
    setViewerTimeZone(Intl.DateTimeFormat().resolvedOptions().timeZone || null);
  }, []);

  const kickoffLabel = viewerTimeZone
    ? formatKickoff(prediction.kickoff_utc, {
        locale,
        timeZone: viewerTimeZone,
        fallback: kickoff_time ?? '',
      })
    : (kickoff_time ?? '');

  const outcomeLabel: Record<Prediction['most_likely'], string> = {
    H: t('predictionCard.outcome.home'),
    D: t('predictionCard.outcome.draw'),
    A: t('predictionCard.outcome.away'),
  };

  return (
    <article className="surface-card flex flex-col gap-5 px-5 py-5 transition-[box-shadow,transform] ease-ease hover:-translate-y-[1px]">
      <header className="flex items-baseline justify-between gap-2 text-2xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="pill">{league_name}</span>
          {prediction.is_live && (
            <span className="pill pill-live">
              <span className="live-dot" aria-hidden="true" />
              {t('predictionCard.badge.live')}
              {prediction.ft_score ? ` · ${prediction.ft_score}` : ''}
            </span>
          )}
          {prediction.pick_correct === true && (
            <span className="pill pill-positive">
              {t('predictionCard.badge.correct')}
              {prediction.ft_score ? ` · ${prediction.ft_score}` : ''}
            </span>
          )}
          {prediction.pick_correct === false && (
            <span className="pill pill-negative">
              {t('predictionCard.badge.incorrect')}
              {prediction.ft_score ? ` · ${prediction.ft_score}` : ''}
            </span>
          )}
        </div>
        <span className="font-mono text-muted" suppressHydrationWarning>
          {formatDate(prediction.date, locale)}
          {kickoffLabel ? ` · ${kickoffLabel}` : ''}
        </span>
      </header>

      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-base font-medium tracking-tight">
          {home_team}
          <span className="px-2 text-muted">{t('predictionCard.vs')}</span>
          {away_team}
        </h3>
      </div>

      <ProbabilityBar
        home={prediction.prob_home}
        draw={prediction.prob_draw}
        away={prediction.prob_away}
        homeLabel={home_team}
        awayLabel={away_team}
      />

      <footer className="flex flex-wrap items-center justify-between gap-3 text-2xs text-muted">
        <span>
          {t('predictionCard.pick')}{' '}
          <span className="text-text">
            {outcomeLabel[prediction.most_likely]}
          </span>
        </span>
        {odds && (
          <span className="font-mono">
            {odds.home.toFixed(2)} · {odds.draw.toFixed(2)} ·{' '}
            {odds.away.toFixed(2)}
          </span>
        )}
      </footer>

      {prediction.stake != null && prediction.stake > 0 ? (
        <div className="flex items-center justify-between text-2xs text-muted">
          <span>{t('predictionCard.stake')}</span>
          <span className="font-mono text-text">
            {prediction.stake_pct != null
              ? `${prediction.stake_pct.toFixed(1)}%`
              : prediction.stake.toFixed(2)}
          </span>
        </div>
      ) : prediction.stake === 0 ? (
        <div className="text-2xs italic text-muted">
          {t('predictionCard.noStake')}
        </div>
      ) : null}
    </article>
  );
}
