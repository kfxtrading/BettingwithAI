import type { League } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

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
