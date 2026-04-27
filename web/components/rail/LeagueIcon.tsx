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
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...props}
    >
      {children}
    </svg>
  );
}

/**
 * Premier League — heraldic crown.
 * Three peaks with orb finials, subtle fill, heavy base bar.
 */
export function PremierLeagueIcon(props: IconProps) {
  return (
    <Base {...props}>
      {/* Crown body */}
      <path
        d="M3.5 16 L4 11.5 L6.5 8.5 L8.5 13 L10 5 L11.5 13 L13.5 8.5 L16 11.5 L16.5 16"
        fill="currentColor"
        fillOpacity={0.13}
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinejoin="round"
      />
      {/* Base bar */}
      <path
        d="M3.5 16 L16.5 16"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
      />
      {/* Orb finials */}
      <circle cx="4" cy="11" r="1.35" fill="currentColor" stroke="none" />
      <circle cx="10" cy="5" r="1.35" fill="currentColor" stroke="none" />
      <circle cx="16" cy="11" r="1.35" fill="currentColor" stroke="none" />
    </Base>
  );
}

/**
 * Bundesliga — football face.
 * Circle outline with filled center pentagon — the canonical black pitch patch.
 */
export function BundesligaIcon(props: IconProps) {
  return (
    <Base {...props} strokeWidth={1.5}>
      {/* Ball */}
      <circle cx="10" cy="10" r="7" stroke="currentColor" fill="none" />
      {/* Center pentagon patch */}
      <path
        d="M10 5.8 L13.9 8.7 L12.4 13.3 L7.6 13.3 L6.1 8.7 Z"
        fill="currentColor"
        fillOpacity={0.88}
        stroke="none"
      />
    </Base>
  );
}

/**
 * Serie A — filled shield.
 * Solid heraldic crest silhouette with subtle inner contour.
 */
export function SerieAIcon(props: IconProps) {
  return (
    <Base {...props} strokeWidth={1.5}>
      {/* Outer shield — filled solid */}
      <path
        d="M10 2 L17 5 V11.5 C17 15 13.8 17.8 10 19 C6.2 17.8 3 15 3 11.5 V5 Z"
        fill="currentColor"
        fillOpacity={0.88}
        stroke="none"
      />
      {/* Inner contour — cut-out highlight for depth */}
      <path
        d="M10 4.5 L15 6.8 V11.5 C15 14 12.8 16.2 10 17.2 C7.2 16.2 5 14 5 11.5 V6.8 Z"
        fill="white"
        fillOpacity={0.14}
        stroke="none"
      />
    </Base>
  );
}

/**
 * La Liga — rising sun over the horizon.
 * Unique to Spanish football: a semicircle, radiating rays, and a solid center.
 */
export function LaLigaIcon(props: IconProps) {
  return (
    <Base {...props} strokeWidth={1.75}>
      {/* Horizon line */}
      <line x1="2.5" y1="13.5" x2="17.5" y2="13.5" strokeLinecap="round" />
      {/* Sun arc */}
      <path
        d="M4.5 13.5 A5.5 5.5 0 0 1 15.5 13.5"
        fill="currentColor"
        fillOpacity={0.11}
        stroke="currentColor"
        strokeWidth={1.5}
      />
      {/* Solid sun center */}
      <circle cx="10" cy="13.5" r="2.3" fill="currentColor" stroke="none" />
      {/* Rays */}
      <line x1="10" y1="4.5" x2="10" y2="7" strokeWidth={1.75} strokeLinecap="round" />
      <line x1="5.2" y1="6.2" x2="6.9" y2="7.9" strokeWidth={1.5} strokeLinecap="round" />
      <line x1="14.8" y1="6.2" x2="13.1" y2="7.9" strokeWidth={1.5} strokeLinecap="round" />
      <line x1="2.5" y1="10.5" x2="5" y2="10.5" strokeWidth={1.5} strokeLinecap="round" />
      <line x1="17.5" y1="10.5" x2="15" y2="10.5" strokeWidth={1.5} strokeLinecap="round" />
    </Base>
  );
}

/**
 * EFL Championship — three ascending chevrons.
 * Conveys promotion and upward momentum; opacity fades toward the base.
 */
export function ChampionshipIcon(props: IconProps) {
  return (
    <Base {...props} strokeWidth={2}>
      <path d="M4 16.5 L10 10.5 L16 16.5" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M4 12 L10 6 L16 12"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.6}
      />
      <path
        d="M4 7.5 L10 1.5 L16 7.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.25}
      />
    </Base>
  );
}

/** Fallback when league code is unknown. */
function GenericIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="10" cy="10" r="6" strokeWidth={1.75} />
    </Base>
  );
}

/** "All leagues" — four equidistant dots in a 2×2 grid. */
export function AllLeaguesIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="6.5" cy="6.5" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="13.5" cy="6.5" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="6.5" cy="13.5" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="13.5" cy="13.5" r="1.5" fill="currentColor" stroke="none" />
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
