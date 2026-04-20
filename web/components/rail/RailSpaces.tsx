'use client';

import { useQuery } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { useLanding } from '@/app/LandingContext';
import { AllLeaguesIcon, LeagueIcon } from './LeagueIcon';

// Accent colour per league, in the same warm/muted family as --accent.
const LEAGUE_ACCENTS: Record<string, string> = {
  BL: '212 101 74',
  PL: '120 95 190',
  SA: '60 130 185',
  LL: '198 72 86',
  ELC: '90 140 100',
  CH: '90 140 100',
  EFL: '90 140 100',
};

function accentFor(code: string): string {
  return LEAGUE_ACCENTS[code.toUpperCase()] ?? '139 139 146';
}

export function RailSpaces() {
  const { t } = useLocale();
  const { league, setLeague } = useLanding();

  const leaguesQuery = useQuery({
    queryKey: queryKeys.leagues,
    queryFn: api.leagues,
  });

  const leagues = leaguesQuery.data ?? [];

  return (
    <div className="flex flex-col gap-1.5">
      <div className="px-3 pt-1 text-2xs uppercase tracking-[0.12em] text-muted">
        {t('rail.section.spaces')}
      </div>
      <ul className="flex flex-col gap-0.5 px-1">
        <li>
          <SpaceRow
            label={t('rail.spaces.all')}
            short=""
            active={league === null}
            onClick={() => setLeague(null)}
            accent="139 139 146"
          >
            <AllLeaguesIcon size={20} />
          </SpaceRow>
        </li>
        {leagues.map((l) => {
          const active = league === l.key;
          return (
            <li key={l.key}>
              <SpaceRow
                label={l.name}
                short={l.key}
                active={active}
                onClick={() => setLeague(l.key)}
                accent={accentFor(l.key)}
              >
                <LeagueIcon code={l.key} size={20} />
              </SpaceRow>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function SpaceRow({
  label,
  short,
  active,
  onClick,
  accent,
  children,
}: {
  label: string;
  short: string;
  active: boolean;
  onClick: () => void;
  accent: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      title={label}
      onClick={onClick}
      className={`focus-ring press group flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ease-ease ${
        active
          ? 'bg-surface text-text shadow-soft'
          : 'text-muted hover:bg-surface-2 hover:text-text'
      }`}
    >
      <span
        className={`flex h-9 w-9 flex-none items-center justify-center rounded-lg transition-colors ease-ease ${
          active ? 'text-white' : 'bg-surface-2'
        }`}
        style={
          active
            ? ({
                background: `rgb(${accent})`,
                boxShadow: `0 4px 10px -6px rgb(${accent} / 0.55)`,
              } as React.CSSProperties)
            : ({
                color: `rgb(${accent})`,
              } as React.CSSProperties)
        }
      >
        {children}
      </span>
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {short && (
        <span className="flex-none text-2xs font-mono uppercase tracking-wide text-muted">
          {short}
        </span>
      )}
    </button>
  );
}
