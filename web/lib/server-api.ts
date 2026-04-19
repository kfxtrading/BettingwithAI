import type {
  BankrollPoint,
  League,
  LeagueSummary,
  PerformanceSummary,
  TodayPayload,
} from './types';

const API_URL =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  'http://localhost:8000';

async function fetchJson<T>(
  path: string,
  revalidate: number,
  fallback: T,
): Promise<T> {
  try {
    const res = await fetch(`${API_URL}${path}`, { next: { revalidate } });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export async function fetchLeaguesServer(): Promise<League[]> {
  try {
    const res = await fetch(`${API_URL}/leagues`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    return (await res.json()) as League[];
  } catch {
    return [];
  }
}

export type LeagueRatingRow = {
  rank: number;
  team: string;
  pi_home: number;
  pi_away: number;
  pi_overall: number;
};

export async function fetchLeagueRatingsServer(
  leagueKey: string,
  top = 30,
): Promise<LeagueRatingRow[]> {
  try {
    const res = await fetch(
      `${API_URL}/leagues/${leagueKey}/ratings?top=${top}`,
      { next: { revalidate: 3600 } },
    );
    if (!res.ok) return [];
    return (await res.json()) as LeagueRatingRow[];
  } catch {
    return [];
  }
}

export type LeagueFixtureRow = {
  date: string;
  home_team: string;
  away_team: string;
  kickoff_time?: string | null;
  prob_home?: number | null;
  prob_draw?: number | null;
  prob_away?: number | null;
  most_likely?: 'H' | 'D' | 'A' | null;
  home_goals?: number | null;
  away_goals?: number | null;
  result?: 'H' | 'D' | 'A' | null;
  pick_correct?: boolean | null;
  slug?: string | null;
};

export type LeagueFixtures = {
  league: string;
  league_name: string;
  next_5: LeagueFixtureRow[];
  last_5: LeagueFixtureRow[];
};

export async function fetchLeagueFixturesServer(
  leagueKey: string,
  limit = 5,
): Promise<LeagueFixtures | null> {
  try {
    const res = await fetch(
      `${API_URL}/leagues/${leagueKey}/fixtures?limit=${limit}`,
      { next: { revalidate: 600 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as LeagueFixtures;
  } catch {
    return null;
  }
}

export async function fetchTodayServer(
  league?: string,
): Promise<TodayPayload | null> {
  const qs = league ? `?league=${encodeURIComponent(league)}` : '';
  return fetchJson<TodayPayload | null>(
    `/predictions/today${qs}`,
    60,
    null,
  );
}

export async function fetchPerformanceSummaryServer(): Promise<PerformanceSummary | null> {
  return fetchJson<PerformanceSummary | null>(
    '/performance/summary',
    300,
    null,
  );
}

export async function fetchBankrollServer(): Promise<BankrollPoint[]> {
  return fetchJson<BankrollPoint[]>('/performance/bankroll', 300, []);
}

export async function fetchLeagueSummariesServer(): Promise<LeagueSummary[]> {
  return fetchJson<LeagueSummary[]>('/leagues/summaries', 3600, []);
}
