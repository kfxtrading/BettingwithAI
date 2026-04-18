import type {
  BankrollPoint,
  FormRow,
  Health,
  League,
  LeagueSummary,
  PerformanceIndex,
  PerformanceSummary,
  RatingRow,
  TeamDetail,
  TodayPayload,
  ValueBet,
} from './types';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`API ${res.status} ${res.statusText} — ${path}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<Health>('/health'),
  leagues: () => request<League[]>('/leagues'),
  leagueSummaries: () => request<LeagueSummary[]>('/leagues/summaries'),
  today: (league?: string) =>
    request<TodayPayload>(
      `/predictions/today${league ? `?league=${league}` : ''}`,
    ),
  valueBets: (league?: string) =>
    request<ValueBet[]>(
      `/value-bets/today${league ? `?league=${league}` : ''}`,
    ),
  ratings: (league: string, top = 20) =>
    request<RatingRow[]>(`/leagues/${league}/ratings?top=${top}`),
  form: (league: string, top = 20) =>
    request<FormRow[]>(`/leagues/${league}/form?top=${top}`),
  performance: () => request<PerformanceSummary>('/performance/summary'),
  bankroll: () => request<BankrollPoint[]>('/performance/bankroll'),
  performanceIndex: () =>
    request<PerformanceIndex>('/performance/index'),
  team: (league: string, team: string) =>
    request<TeamDetail>(
      `/teams/${league}/${encodeURIComponent(team)}`,
    ),
};

export const queryKeys = {
  health: ['health'] as const,
  leagues: ['leagues'] as const,
  leagueSummaries: ['leagues', 'summaries'] as const,
  today: (league?: string) => ['today', league ?? 'all'] as const,
  ratings: (league: string, top: number) =>
    ['ratings', league, top] as const,
  form: (league: string, top: number) => ['form', league, top] as const,
  performance: ['performance'] as const,
  bankroll: ['bankroll'] as const,
  performanceIndex: ['performance', 'index'] as const,
  team: (league: string, team: string) => ['team', league, team] as const,
};
