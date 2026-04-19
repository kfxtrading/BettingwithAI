export type Dictionary = Record<DictionaryKey, string>;

export type DictionaryKey =
  | 'site.title'
  | 'site.tagline'
  | 'site.description'
  | 'home.heading'
  | 'home.subheading'
  | 'leagues.heading'
  | 'leagues.description'
  | 'performance.heading'
  | 'performance.description';

export const en: Dictionary = {
  'site.title': 'Betting with AI',
  'site.tagline':
    "Today's AI-driven betting analyses for the Top 5 football leagues.",
  'site.description':
    'Data-driven football predictions and value bets for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship. CatBoost + Poisson + MLP ensemble with transparent performance tracking.',
  'home.heading': "Today's betting analyses for the Top 5 leagues.",
  'home.subheading':
    'Calibrated probabilities for Home, Draw, Away — plus value bets where the model disagrees with the market.',
  'leagues.heading': 'Pi-Ratings and form across every top league.',
  'leagues.description':
    'Browse Pi-Ratings, recent form and head-to-head data for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship.',
  'performance.heading': 'Performance across the entire betting history.',
  'performance.description':
    'Full transparency over hit rate, ROI, max drawdown and per-league breakdowns — updated after every matchday.',
};
