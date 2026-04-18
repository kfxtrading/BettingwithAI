import type { ValueBet } from '@/lib/types';

const confidenceLabel: Record<ValueBet['confidence'], string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

const confidenceTone: Record<ValueBet['confidence'], string> = {
  high: 'pill-positive',
  medium: 'pill-accent',
  low: 'pill',
};

export function ValueBetBadge({ bet }: { bet: ValueBet }) {
  return (
    <article className="surface-card flex min-w-[260px] flex-col gap-4 px-5 py-5">
      <header className="flex items-baseline justify-between text-2xs">
        <span className="pill">{bet.league_name}</span>
        <span className={`pill ${confidenceTone[bet.confidence]}`}>
          {confidenceLabel[bet.confidence]}
        </span>
      </header>

      <div>
        <h3 className="text-base font-medium tracking-tight">
          {bet.home_team}
          <span className="px-2 text-muted">vs</span>
          {bet.away_team}
        </h3>
        <p className="mt-1 text-sm text-muted">{bet.bet_label}</p>
      </div>

      <dl className="grid grid-cols-3 gap-3 font-mono text-2xs">
        <div>
          <dt className="text-muted">Odds</dt>
          <dd className="mt-0.5 text-sm">{bet.odds.toFixed(2)}</dd>
        </div>
        <div>
          <dt className="text-muted">Edge</dt>
          <dd className="mt-0.5 text-sm text-accent">
            +{bet.edge_pct.toFixed(1)}%
          </dd>
        </div>
        <div>
          <dt className="text-muted">Stake</dt>
          <dd className="mt-0.5 text-sm">{bet.kelly_stake.toFixed(2)}</dd>
        </div>
      </dl>
    </article>
  );
}
