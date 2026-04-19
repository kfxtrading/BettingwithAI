import Link from 'next/link';
import { localizedPath } from '@/lib/seo';
import { getDictionary } from '@/lib/i18n';
import type { Locale } from '@/lib/i18n';
import type { LeagueFixtureRow, LeagueFixtures } from '@/lib/server-api';

type Props = {
  locale: Locale;
  leagueKey: string;
  fixtures: LeagueFixtures | null;
};

function formatProb(p?: number | null): string {
  if (p === null || p === undefined) return '—';
  return `${Math.round(p * 100)}%`;
}

function pickLabel(row: LeagueFixtureRow): string {
  if (row.most_likely === 'H') return row.home_team;
  if (row.most_likely === 'A') return row.away_team;
  if (row.most_likely === 'D') return 'Draw';
  return '—';
}

export function LeagueFixturesWidget({ locale, leagueKey, fixtures }: Props) {
  const dict = getDictionary(locale);
  const next = fixtures?.next_5 ?? [];
  const last = fixtures?.last_5 ?? [];

  return (
    <section className="grid gap-6 md:grid-cols-2">
      <div>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-muted">
          {dict['leagueHub.next5.title']}
        </h2>
        {next.length === 0 ? (
          <p className="surface-card px-4 py-3 text-sm text-muted">
            {dict['leagueHub.next5.empty']}
          </p>
        ) : (
          <ul className="space-y-2">
            {next.map((row) => (
              <li
                key={`${row.date}-${row.home_team}-${row.away_team}`}
                className="surface-card px-4 py-3"
              >
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-medium text-text">
                    {row.home_team} <span className="text-muted">vs</span>{' '}
                    {row.away_team}
                  </span>
                  <time
                    className="font-mono text-2xs uppercase tracking-[0.08em] text-muted"
                    dateTime={row.date}
                  >
                    {row.date}
                    {row.kickoff_time ? ` · ${row.kickoff_time}` : ''}
                  </time>
                </div>
                <div className="mt-2 flex items-center justify-between gap-3 text-2xs uppercase tracking-[0.08em] text-muted">
                  <span>
                    {formatProb(row.prob_home)} · {formatProb(row.prob_draw)} ·{' '}
                    {formatProb(row.prob_away)}
                  </span>
                  <span className="text-text">{pickLabel(row)}</span>
                </div>
                {row.slug && (
                  <p className="mt-2">
                    <Link
                      href={localizedPath(
                        locale,
                        `/leagues/${leagueKey}/${row.slug}`,
                      )}
                      hrefLang={locale}
                      className="focus-ring text-2xs uppercase tracking-[0.08em] text-accent"
                    >
                      {dict['leagueHub.viewMatch']}
                    </Link>
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-muted">
          {dict['leagueHub.last5.title']}
        </h2>
        {last.length === 0 ? (
          <p className="surface-card px-4 py-3 text-sm text-muted">
            {dict['leagueHub.last5.empty']}
          </p>
        ) : (
          <ul className="space-y-2">
            {last.map((row) => {
              const score =
                row.home_goals !== null && row.away_goals !== null
                  ? `${row.home_goals}-${row.away_goals}`
                  : '—';
              const correctness =
                row.pick_correct === true
                  ? `✓ ${dict['leagueHub.pickCorrect']}`
                  : row.pick_correct === false
                  ? `✗ ${dict['leagueHub.pickIncorrect']}`
                  : null;
              return (
                <li
                  key={`${row.date}-${row.home_team}-${row.away_team}`}
                  className="surface-card px-4 py-3"
                >
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <span className="font-medium text-text">
                      {row.home_team} <span className="text-muted">vs</span>{' '}
                      {row.away_team}
                    </span>
                    <time
                      className="font-mono text-2xs uppercase tracking-[0.08em] text-muted"
                      dateTime={row.date}
                    >
                      {row.date}
                    </time>
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3 text-2xs uppercase tracking-[0.08em] text-muted">
                    <span className="font-mono text-text">{score}</span>
                    {correctness && (
                      <span
                        className={
                          row.pick_correct
                            ? 'text-accent'
                            : 'text-muted'
                        }
                      >
                        {correctness}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
