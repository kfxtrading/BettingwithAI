import type { ReactNode, SVGProps } from 'react';

type IconProps = Omit<SVGProps<SVGSVGElement>, 'children'> & {
  size?: number;
};

function Base({
  size = 18,
  children,
  ...props
}: IconProps & { children: ReactNode }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...props}
    >
      {children}
    </svg>
  );
}

/** Bundesliga — double chevron. */
export function BundesligaIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M3.5 13 L10 5.5 L16.5 13" />
      <path d="M6.5 15 L10 10.5 L13.5 15" opacity={0.6} />
    </Base>
  );
}

/** Premier League — three-peak crown. */
export function PremierLeagueIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M3 8 L6 12 L10 5 L14 12 L17 8 L15.5 15.5 H4.5 Z" />
      <path d="M4.5 15.5 H15.5" opacity={0.6} />
    </Base>
  );
}

/** Serie A — shield / crest. */
export function SerieAIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M10 3 L16 5.5 V11 C16 13.8 13.3 16.2 10 17 C6.7 16.2 4 13.8 4 11 V5.5 Z" />
      <path d="M10 8 V13" opacity={0.55} />
    </Base>
  );
}

/** La Liga — sunburst / 8-ray star. */
export function LaLigaIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="10" cy="10" r="3" />
      <path d="M10 2.5 V5" />
      <path d="M10 15 V17.5" />
      <path d="M2.5 10 H5" />
      <path d="M15 10 H17.5" />
      <path d="M4.7 4.7 L6.5 6.5" opacity={0.75} />
      <path d="M13.5 13.5 L15.3 15.3" opacity={0.75} />
      <path d="M15.3 4.7 L13.5 6.5" opacity={0.75} />
      <path d="M6.5 13.5 L4.7 15.3" opacity={0.75} />
    </Base>
  );
}

/** EFL Championship — ascending promotion ladder. */
export function ChampionshipIcon(props: IconProps) {
  return (
    <Base {...props}>
      <rect x="3" y="12" width="3.5" height="5" rx="0.5" />
      <rect x="8.25" y="8" width="3.5" height="9" rx="0.5" />
      <rect x="13.5" y="4" width="3.5" height="13" rx="0.5" />
    </Base>
  );
}

/** Fallback when league code is unknown. */
function GenericIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="10" cy="10" r="5" />
    </Base>
  );
}

/** "All leagues" — four-dot grid. */
export function AllLeaguesIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="6.5" cy="6.5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="13.5" cy="6.5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="6.5" cy="13.5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="13.5" cy="13.5" r="1.4" fill="currentColor" stroke="none" />
    </Base>
  );
}

const ICON_MAP: Record<string, (p: IconProps) => JSX.Element> = {
  BL: BundesligaIcon,
  PL: PremierLeagueIcon,
  SA: SerieAIcon,
  LL: LaLigaIcon,
  ELC: ChampionshipIcon,
  CH: ChampionshipIcon,
  EFL: ChampionshipIcon,
};

export function LeagueIcon({
  code,
  ...props
}: IconProps & { code: string }) {
  const Icon = ICON_MAP[code.toUpperCase()] ?? GenericIcon;
  return <Icon {...props} />;
}
