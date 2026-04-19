'use client';

import type { Confidence, ValueBet } from '@/lib/types';
import { useLocale } from '@/lib/i18n/LocaleProvider';

const confidenceTone: Record<Confidence, string> = {
  high: 'pill-positive',
  medium: 'pill-accent',
  low: 'pill',
};

const confidenceRank: Record<Confidence, number> = {
  low: 0,
  medium: 1,
  high: 2,
};

function topConfidence(bets: ValueBet[]): Confidence {
  return bets.reduce<Confidence>(
    (acc, b) => (confidenceRank[b.confidence] > confidenceRank[acc] ? b.confidence : acc),
    'low',
  );
}

export function ValueBetBadge({ bets }: { bets: ValueBet[] }) {
  const { t } = useLocale();
  const confidenceLabel: Record<Confidence, string> = {
    high: t('valueBet.confidence.high'),
    medium: t('valueBet.confidence.medium'),
    low: t('valueBet.confidence.low'),
  };

  if (bets.length === 0) return null;
  const first = bets[0];
  const sorted = [...bets].sort((a, b) => b.edge - a.edge);
  const headerConfidence = topConfidence(sorted);

  return (
    <article className="surface-card flex min-w-[260px] flex-col gap-4 px-5 py-5">
      <header className="flex items-baseline justify-between text-2xs">
        <span className="pill">{first.league_name}</span>
        <span className={`pill ${confidenceTone[headerConfidence]}`}>
          {confidenceLabel[headerConfidence]}
        </span>
      </header>

      <div>
        <h3 className="text-base font-medium tracking-tight">
          {first.home_team}
          <span className="px-2 text-muted">vs</span>
          {first.away_team}
        </h3>
      </div>

      <ul className="flex flex-col divide-y divide-border/40">
        {sorted.map((bet, i) => (
          <li
            key={`${bet.outcome}-${bet.bet_label}-${i}`}
            className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0"
          >
            <p className="text-sm text-muted">{bet.bet_label}</p>
            <dl className="grid grid-cols-3 gap-3 font-mono text-2xs">
              <div>
                <dt className="text-muted">{t('valueBet.odds')}</dt>
                <dd className="mt-0.5 text-sm">{bet.odds.toFixed(2)}</dd>
              </div>
              <div>
                <dt className="text-muted">{t('valueBet.edge')}</dt>
                <dd className="mt-0.5 text-sm text-accent">
                  +{bet.edge_pct.toFixed(1)}%
                </dd>
              </div>
              <div>
                <dt className="text-muted">{t('valueBet.stake')}</dt>
                <dd className="mt-0.5 text-sm">{bet.kelly_stake.toFixed(2)}</dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
    </article>
  );
}
