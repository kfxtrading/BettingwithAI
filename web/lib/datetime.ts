/**
 * Date/time helpers with DST awareness.
 *
 * Backend delivers kickoffs as UTC ISO strings (suffix "Z"). We rely on the
 * browser's Intl.DateTimeFormat to render them in a target timezone — it
 * automatically handles summer/winter time transitions via the IANA tz db.
 */

type FormatKickoffOptions = {
  locale?: string;
  /** IANA timezone, e.g. "Europe/Berlin". Defaults to the user's browser tz. */
  timeZone?: string;
  /** Append short tz label (e.g. "CET", "CEST"). */
  showTimeZoneName?: boolean;
  /** Fallback HH:MM string to show if the UTC ISO is missing. */
  fallback?: string | null;
};

/**
 * Render a kickoff time. Prefers the UTC ISO; falls back to the league-local
 * HH:MM string already shipped in the snapshot for backwards compatibility.
 */
export function formatKickoff(
  utcIso: string | null | undefined,
  opts: FormatKickoffOptions = {},
): string {
  const { locale, timeZone, showTimeZoneName = false, fallback = null } = opts;
  if (!utcIso) return fallback ?? '';
  const d = new Date(utcIso);
  if (Number.isNaN(d.getTime())) return fallback ?? '';
  const fmtOpts: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  };
  if (timeZone) fmtOpts.timeZone = timeZone;
  if (showTimeZoneName) fmtOpts.timeZoneName = 'short';
  try {
    return new Intl.DateTimeFormat(locale, fmtOpts).format(d);
  } catch {
    return fallback ?? '';
  }
}

/**
 * Parse a ``YYYY-MM-DD`` string as a local calendar day (not UTC midnight).
 * Prevents the "off-by-one-day" bug caused by ``new Date("2025-03-30")``
 * being interpreted as UTC by JavaScript.
 */
export function parseLocalDate(dateStr: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr);
  if (!m) return null;
  const [, y, mo, d] = m;
  return new Date(Number(y), Number(mo) - 1, Number(d));
}

/** Format a ``YYYY-MM-DD`` date string using the user's locale. */
export function formatMatchDate(
  dateStr: string | null | undefined,
  locale?: string,
  opts: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: '2-digit' },
): string {
  if (!dateStr) return '';
  const d = parseLocalDate(dateStr);
  if (!d) return dateStr;
  try {
    return new Intl.DateTimeFormat(locale, opts).format(d);
  } catch {
    return dateStr;
  }
}
