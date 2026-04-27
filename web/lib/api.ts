import type {
  BankrollPoint,
  FormRow,
  Health,
  HistoryPayload,
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
  history: (days = 14) => request<HistoryPayload>(`/history?days=${days}`),
  getConsent: () => request<ConsentRecord | null>('/consent'),
  saveConsent: (payload: ConsentPayload) =>
    request<ConsentRecord>('/consent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  supportAsk: (payload: SupportAskPayload) =>
    request<SupportAskResponse>('/support/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
};

export type ConsentCategory = 'necessary' | 'analytics' | 'marketing';

export interface ConsentPayload {
  accepted: boolean;
  categories: ConsentCategory[];
  version?: string;
}

export interface ConsentRecord {
  accepted: boolean;
  categories: ConsentCategory[];
  version: string;
  updated_at: string;
  first_seen_at: string;
}

export interface SupportAskPayload {
  question: string;
  lang: string;
  top_k?: number;
}

export interface SupportPrediction {
  intent_id: string;
  chapter: string;
  score: number;
  chapter_score: number;
}

export interface MatchNewsItem {
  title: string;
  url: string;
  source: string;
}

export interface MatchContext {
  home_team: string;
  away_team: string;
  league: string;
  league_name: string;
  kickoff_time: string | null;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  most_likely: 'H' | 'D' | 'A';
  odds: { home: number; draw: number; away: number; bookmaker: string } | null;
  form_home: string | null;
  form_away: string | null;
  value_bet: boolean;
  news: MatchNewsItem[];
}

export interface SupportAskResponse {
  lang: string;
  question: string;
  predictions: SupportPrediction[];
  fallback: boolean;
  match_context: MatchContext | null;
}

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
  history: (days: number) => ['history', days] as const,
};
