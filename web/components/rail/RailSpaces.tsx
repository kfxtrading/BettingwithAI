'use client';

import { useQuery } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { api, queryKeys } from '@/lib/api';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { useLanding } from '@/app/LandingContext';
import { AllLeaguesIcon, LeagueIcon } from './LeagueIcon';

// Each league gets a refined, slightly-muted colour that sits well inside
// the warm design system without looking like a generic betting site palette.
const LEAGUE_ACCENTS: Record<string, string> = {
  PL: '102 78 188',   // imperial purple
  BL: '192 32 48',   // Bundesliga red
  SA: '22 82 162',   // Serie A deep blue
  LL: '195 88 28',   // La Liga amber-orange
  ELC: '30 128 82',  // EFL Championship forest green
  CH: '30 128 82',
  EFL: '30 128 82',
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
        className={`flex h-9 w-9 flex-none items-center justify-center rounded-xl transition-all duration-200 ease-ease ${
          active
            ? 'text-white'
            : 'bg-surface-2 ring-1 ring-inset ring-black/[0.07] dark:ring-white/[0.09]'
        }`}
        style={
          active
            ? ({
                background: `linear-gradient(150deg, rgb(${accent} / 0.82) 0%, rgb(${accent}) 100%)`,
                boxShadow: `0 4px 14px -4px rgb(${accent} / 0.45), inset 0 1px 0 rgba(255,255,255,0.22)`,
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
        <span
          className="flex-none rounded px-1 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted/70"
          style={active ? { color: `rgb(${accent})` } : undefined}
        >
          {short}
        </span>
      )}
    </button>
  );
}
