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
      <div className="flex flex-wrap gap-1.5 px-2">
        <SpaceButton
          label={t('rail.spaces.all')}
          active={league === null}
          onClick={() => setLeague(null)}
          accent="139 139 146"
        >
          <AllLeaguesIcon size={18} />
        </SpaceButton>
        {leagues.map((l) => {
          const active = league === l.key;
          return (
            <SpaceButton
              key={l.key}
              label={l.name}
              active={active}
              onClick={() => setLeague(l.key)}
              accent={accentFor(l.code)}
            >
              <LeagueIcon code={l.code} size={18} />
            </SpaceButton>
          );
        })}
      </div>
    </div>
  );
}

function SpaceButton({
  label,
  active,
  onClick,
  accent,
  children,
}: {
  label: string;
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
      className={`focus-ring press relative flex h-9 w-9 items-center justify-center rounded-xl transition-colors ease-ease ${
        active
          ? 'text-white shadow-soft'
          : 'bg-surface-2 text-muted hover:text-text'
      }`}
      style={
        active
          ? ({
              background: `rgb(${accent})`,
              boxShadow: `0 4px 12px -6px rgb(${accent} / 0.55)`,
            } as React.CSSProperties)
          : ({
              color: `rgb(${accent})`,
            } as React.CSSProperties)
      }
    >
      {children}
    </button>
  );
}
