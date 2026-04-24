import type { FaqItem } from './home-faq';

export const LEAGUES_INDEX_FAQ: readonly FaqItem[] = [
  {
    question: 'Which leagues are covered?',
    answer:
      'The platform covers the Top 5 European leagues — English Premier League, Spanish La Liga, German Bundesliga, Italian Serie A and French Ligue 1 — plus the English EFL Championship and Swiss Super League. Coverage is intentionally narrow: every supported league has at least 10 years of historical Football-Data.co.uk results, stable market odds and a separately tuned ensemble, so predictions remain calibrated.',
  },
  {
    question: 'Why only the Top 5 leagues?',
    answer:
      'Methodological honesty. A calibrated ensemble needs thousands of historical matches per league with consistent referee standards, lineup availability and closing odds. Lower-tier and non-European competitions either miss one of those ingredients or require a separately tuned model. Rather than ship weaker predictions for visibility, the site limits coverage to leagues where the model genuinely has an edge.',
  },
  {
    question: 'How are Pi-Ratings different from Elo?',
    answer:
      'Pi-Ratings are an Elo successor introduced by Constantinou & Fenton (2013) with two innovations: separate home and away ratings per team, and a non-linear goal-difference update. The result is faster convergence after promotions, better adaptation to home-advantage drift and higher Brier-score accuracy on out-of-sample matches. The platform uses Pi-Ratings as one of ~70 engineered features rather than as a stand-alone predictor.',
  },
  {
    question: 'How often is each league’s data refreshed?',
    answer:
      'Match results and market odds are refreshed once per day after the previous matchday closes. Pi-Ratings update incrementally with each new result. The weekly fixtures list refreshes every hour. Live scores (while matches are in progress) refresh every 20–30 seconds.',
  },
  {
    question: 'Are lineups and injuries factored in?',
    answer:
      'Optionally. When the Sofascore integration is enabled, confirmed lineups, missing-player signals and referee assignments are injected as features one to two hours before kick-off. The feature importance of lineup-aware variables is around 4–6 % of total model gain, so predictions remain meaningful even without them.',
  },
];

export const LEAGUE_DETAIL_FAQ: readonly FaqItem[] = [
  {
    question: 'What do the Pi-Rating numbers mean?',
    answer:
      'Each team has two Pi-Ratings — home and away — expressed roughly on a 0–3 scale. A higher number means a stronger expected goal-difference output in that context. The numbers are calibrated so that a 0.5-point gap translates into roughly a one-third of a goal expected margin at neutral venue. Use the difference between ratings, not absolute values, to estimate match competitiveness.',
  },
  {
    question: 'How is recent form weighted?',
    answer:
      'Form is captured separately from Pi-Ratings through a 5-match rolling window of expected-goals-for, expected-goals-against and shots on target. The ensemble then learns how much weight to put on form versus long-term rating — typically around 15–20 % of total decision weight, rising after international breaks when the long-term model is stalest.',
  },
  {
    question: 'Where do the probabilities come from?',
    answer:
      'Probabilities are the final, calibrated output of a CatBoost + Poisson + MLP ensemble, weighted by Dirichlet priors tuned per league on a held-out season, then isotonic-calibrated so that stated probabilities match observed frequencies within 1.5 % expected calibration error.',
  },
  {
    question: 'Why does the pick sometimes disagree with the highest probability?',
    answer:
      'The pick is always the outcome with the highest model probability. When it disagrees with the market favourite, the model has found an edge big enough to overturn the bookmaker — that is the definition of a value bet. Both numbers are shown so you can decide.',
  },
];

export const PERFORMANCE_FAQ: readonly FaqItem[] = [
  {
    question: 'How is accuracy measured?',
    answer:
      'Primary metric is the Ranked Probability Score (RPS), which penalises probability distributions for mis-ordering outcomes rather than just mis-classifying them. Secondary metrics are Brier score, log-loss and classification accuracy. ROI and Closing Line Value (CLV) measure financial performance against closing odds. All numbers are walk-forward out-of-sample — no in-sample statistics are shown.',
  },
  {
    question: 'What is Closing Line Value (CLV)?',
    answer:
      'CLV is the difference between the odds you bet at and the closing odds right before kick-off. Positive average CLV is the strongest leading indicator that a bettor has a genuine edge, because closing odds are the most efficient price the market will produce. The performance tracker reports rolling CLV on every closed bet.',
  },
  {
    question: 'Why does ROI fluctuate so much?',
    answer:
      'Sports betting is high-variance. A 3 % edge with fractional-Kelly sizing typically shows swings of ±15 % over any 100-bet window, even when the underlying edge is real. The platform shows 50-, 100- and 250-bet rolling ROI so you can separate long-run signal from short-run noise.',
  },
  {
    question: 'Are past results ever edited?',
    answer:
      'Never. Once a bet is recorded in the daily snapshot and the match has kicked off, the entry is immutable. Post-match the row is annotated with the actual result, stake PnL and CLV, but predictions and stakes are frozen. The full history is visible on the performance tracker.',
  },
];
