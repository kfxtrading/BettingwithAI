export type FaqItem = { question: string; answer: string };

/** Last editorial review of the FAQ content (ISO yyyy-mm-dd). */
export const HOME_FAQ_LAST_UPDATED = '2026-04-24';

/**
 * Homepage FAQ — optimised for GEO (LLM citation) and Google FAQ rich results.
 * One question per item, direct answer first, context second, 60–140 words each.
 * Language: English only (EN fallback across locales).
 */
export const HOME_FAQ: readonly FaqItem[] = [
  {
    question: 'What is Betting with AI?',
    answer:
      'Betting with AI is an independent, non-affiliate football analytics platform. It publishes calibrated 1X2 probabilities, expected-value bets and Kelly-sized stake recommendations for the Top 5 European leagues — Premier League, La Liga, Bundesliga, Serie A and Ligue 1. The model is a CatBoost gradient-boosting classifier combined with a Dixon-Coles Poisson goal model and a PyTorch MLP, blended through a Dirichlet-tuned ensemble and calibrated with isotonic regression. All predictions are generated from the same pipeline publicly tracked on the performance page.',
  },
  {
    question: 'How does AI-based football prediction work on this site?',
    answer:
      'The pipeline ingests ~10 years of historical match data, current-season form, Pi-Ratings (an Elo successor tuned for football), market odds and optional Sofascore context. Each model outputs home / draw / away probabilities. A Dirichlet-weighted ensemble blends them, and isotonic calibration rescales the distribution so that the stated probabilities match observed frequencies (Expected Calibration Error < 1.5%). Value bets are flagged when the model probability exceeds the market-implied probability (after margin removal) by at least 3 percentage points.',
  },
  {
    question: 'What is a value bet?',
    answer:
      'A value bet is any wager whose true probability of winning exceeds the bookmaker’s implied probability. Mathematically, (probability × decimal odds) must be greater than 1 — the product is the expected value. Value bets are positive in expectation, not in any single match, and only profitable over hundreds of bets. The platform surfaces value bets after removing the 4–8% bookmaker margin from the market odds, so what is shown is the genuine edge versus the fair price.',
  },
  {
    question: 'How accurate are the predictions?',
    answer:
      'Accuracy is measured with the Ranked Probability Score (RPS), Brier score and log-loss, all reported on out-of-sample walk-forward backtests. The current ensemble hits an RPS between 0.195 and 0.210 depending on the league — competitive with the best publicly known models. A transparent live tracker on the performance page shows every closed bet, Closing Line Value (CLV) and rolling ROI, updated after each completed matchday so nothing is cherry-picked.',
  },
  {
    question: 'Which data sources are used?',
    answer:
      'Primary data comes from Football-Data.co.uk match results and market closing odds. Pi-Ratings are computed in-house. Optional enrichment from Sofascore (lineups, missing players, referee) runs only when explicitly enabled and rate-limited to 25 seconds per request. Weather context, where relevant, is pulled from public forecast APIs. No scraping runs without the `SCRAPING_ENABLED=1` opt-in, so data use is conservative and the model remains reproducible from the public CSV feeds alone.',
  },
  {
    question: 'How is the Kelly criterion used for stakes?',
    answer:
      'Every value bet gets a fractional Kelly stake, capped at 25–50 % of full Kelly. Full Kelly maximises the long-run geometric growth rate of the bankroll but is too volatile for a real human to stomach and too aggressive when model probabilities are uncertain. Fractional Kelly preserves most of the growth advantage while keeping drawdowns manageable. Stakes are expressed in percentage of bankroll, never in currency, so the system scales to any bankroll size.',
  },
  {
    question: 'Is the service free?',
    answer:
      'Yes. Core features — today’s predictions, value bets, Kelly stakes, league overview and the full performance tracker — are free to use without registration and without affiliate redirects. The site does not sell tips, does not take a cut from bookmakers, and does not place bets for users. It is an analytics tool, not a wagering platform.',
  },
  {
    question: 'How does Betting with AI compare to Forebet and Sofascore?',
    answer:
      'Forebet is a long-running prediction site optimised for hand-written Poisson previews and SEO volume; Sofascore is a scores and stats aggregator, not a prediction tool. Betting with AI is narrower in scope: only the Top 5 European leagues, but every prediction is a calibrated probability distribution from an ensemble model, every value bet has an explicit Kelly stake, and every past bet is tracked publicly with ROI and CLV. The aim is methodological transparency, not content volume.',
  },
  {
    question: 'Why CatBoost instead of XGBoost or logistic regression?',
    answer:
      'CatBoost handles categorical features (team, referee, stadium, kickoff day-of-week) natively without lossy one-hot encoding and is robust to the class imbalance typical in 1X2 football markets. On our walk-forward backtests, CatBoost beats XGBoost by roughly 0.003 RPS and logistic regression by roughly 0.012 RPS, with identical calibration and shorter training time. The gradient-boosted output is further blended with the Dixon-Coles Poisson model, which anchors predictions to the goal-generating process.',
  },
  {
    question: 'How often is the snapshot updated?',
    answer:
      'A fresh snapshot is generated each day, typically between 08:00 and 09:00 UTC once the latest odds are available. Value bets use the closing odds from the snapshot time, so displayed edges are conservative rather than optimistic. If you arrive before the daily snapshot has finished, an explicit stale-notice is shown and no stale numbers are served. Live matches are refreshed every 20–30 seconds while a game is in progress.',
  },
];
