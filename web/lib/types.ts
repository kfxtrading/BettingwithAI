// Mirrors src/football_betting/api/schemas.py
export type Outcome = 'H' | 'D' | 'A';
export type Confidence = 'low' | 'medium' | 'high';

export interface Odds {
  home: number;
  draw: number;
  away: number;
  bookmaker: string;
}

export interface Prediction {
  date: string;
  league: string;
  league_name: string;
  home_team: string;
  away_team: string;
  kickoff_time: string | null;
  kickoff_utc?: string | null;
  league_timezone?: string | null;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  odds: Odds | null;
  model_name: string;
  most_likely: Outcome;
  is_live?: boolean;
  pick_correct?: boolean | null;
  ft_score?: string | null;
}

export interface ValueBet {
  date: string;
  league: string;
  league_name: string;
  home_team: string;
  away_team: string;
  outcome: Outcome;
  bet_label: string;
  odds: number;
  model_prob: number;
  market_prob: number;
  edge: number;
  edge_pct: number;
  kelly_stake: number;
  expected_value_pct: number;
  confidence: Confidence;
}

export interface League {
  key: string;
  name: string;
  code: string;
  avg_goals_per_team: number;
  home_advantage: number;
}

export interface LeagueSummary {
  league: string;
  league_name: string;
  leader: string | null;
  leader_rating: number | null;
  n_teams: number;
}

export interface RatingRow {
  rank: number;
  team: string;
  pi_home: number;
  pi_away: number;
  pi_overall: number;
}

export interface FormRow {
  team: string;
  last5: string;
  points: number;
  goals_for: number;
  goals_against: number;
}

export interface TeamDetail {
  team: string;
  league: string;
  pi_home: number;
  pi_away: number;
  pi_overall: number;
  last10: string;
  goals_for_avg: number;
  goals_against_avg: number;
}

export interface PerformancePerLeague {
  league: string;
  league_name: string;
  n_bets: number;
  hit_rate: number;
  roi: number;
}

export interface StrategyStats {
  n_bets: number;
  hit_rate: number;
  roi: number;
  total_profit: number;
  total_stake: number;
  max_drawdown_pct: number;
}

export interface PerformanceSummary {
  n_predictions: number;
  n_bets: number;
  hit_rate: number;
  roi: number;
  total_profit: number;
  total_stake: number;
  brier_mean: number | null;
  rps_mean: number | null;
  max_drawdown_pct: number;
  per_league: PerformancePerLeague[];
  value_bets?: StrategyStats | null;
  predictions?: StrategyStats | null;
}

export interface BankrollPoint {
  date: string;
  value: number;
  value_bets?: number | null;
  predictions?: number | null;
}

export interface EquityIndexPoint {
  date: string;
  index: number;
  n_bets_cumulative: number;
}

export interface PerformanceIndex {
  updated_at: string;
  tracking_started_at: string;
  n_days_tracked: number;
  n_bets: number;
  hit_rate: number | null;
  current_index: number;
  all_time_high_index: number;
  max_drawdown_pct: number;
  current_drawdown_pct: number;
  equity_curve: EquityIndexPoint[];
  rule_hash: string;
  model_version: string;
}

export interface TodayPayload {
  generated_at: string;
  predictions: Prediction[];
  value_bets: ValueBet[];
}

export interface ModelAvailability {
  catboost: boolean;
  mlp: boolean;
}

export interface Health {
  status: 'ok';
  version: string;
  models_available: Record<string, ModelAvailability>;
  snapshot_present: boolean;
}

export type BetStatus = 'won' | 'lost' | 'pending';
export type BetKind = 'value' | 'prediction';

export interface GradedBet {
  date: string;
  league: string;
  league_name: string;
  home_team: string;
  away_team: string;
  outcome: Outcome;
  bet_label: string;
  odds: number;
  stake: number;
  ft_result: Outcome | null;
  ft_score: string | null;
  status: BetStatus;
  pnl: number;
  kind?: BetKind;
}

export interface HistoryDay {
  date: string;
  n_bets: number;
  n_won: number;
  n_lost: number;
  n_pending: number;
  pnl: number;
  bets: GradedBet[];
}

export interface HistoryPayload {
  generated_at: string;
  n_days: number;
  total_bets: number;
  total_won: number;
  total_lost: number;
  total_pending: number;
  total_pnl: number;
  hit_rate: number | null;
  days: HistoryDay[];
}
