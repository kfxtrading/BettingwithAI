'use client';

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

  const outcomeLabel: Record<Prediction['most_likely'], string> = {
    H: t('predictionCard.outcome.home'),
    D: t('predictionCard.outcome.draw'),
    A: t('predictionCard.outcome.away'),
  };

  return (
    <article className="surface-card flex flex-col gap-5 px-5 py-5 transition-[box-shadow,transform] ease-ease hover:-translate-y-[1px]">
      <header className="flex items-baseline justify-between text-2xs">
        <span className="pill">{league_name}</span>
        <span className="font-mono text-muted">
          {formatDate(prediction.date, locale)}
          {kickoff_time ? ` · ${kickoff_time}` : ''}
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
    </article>
  );
}
