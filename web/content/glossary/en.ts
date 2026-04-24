export type GlossaryEntry = {
  slug: string;
  term: string;
  /** One-sentence definition used in meta description and LLM snippets. */
  shortDefinition: string;
  /** 150–250 word full definition rendered on the detail page. */
  body: string;
  /** Optional symbol or abbreviation. */
  termCode?: string;
  /** Related entries (slugs) for internal linking. */
  related?: string[];
  lastUpdated: string;
};

const LAST_UPDATED = '2026-04-24';

export const GLOSSARY_ENTRIES: readonly GlossaryEntry[] = [
  {
    slug: 'value-bet',
    term: 'Value bet',
    shortDefinition:
      'A wager whose true probability of winning exceeds the bookmaker’s implied probability, giving positive expected value.',
    body:
      'A value bet is any wager where the estimated probability of the outcome, multiplied by the decimal odds, is greater than one. The product is the expected value (EV), and a value bet is by definition any bet with EV above 1.0. The market’s implied probability is 1 / decimal_odds, but raw 1X2 odds carry a 4–8 percent bookmaker margin; to compare honestly, the three implied probabilities must be normalised to sum to 1.0 before the edge is measured. Value betting is the only long-run profitable strategy in sports betting because it is agnostic to whether the favourite or the underdog wins — a 1.20 favourite at 90 percent true probability has EV 1.08, while a 4.50 underdog at 25 percent true probability has EV 1.125. The underdog is the better value bet despite being much less likely. Short-term outcomes are noisy; value bets only become profitable over hundreds of wagers with disciplined staking.',
    related: ['expected-value', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'expected-value',
    term: 'Expected value (EV)',
    shortDefinition:
      'The average profit or loss of a bet per unit staked, computed as probability × odds minus one.',
    termCode: 'EV',
    body:
      'Expected value (EV) is the long-run average outcome of a repeated bet, expressed per unit staked. For a decimal-odds wager the formula is EV = p × odds − 1, where p is the true probability of winning. A positive EV means that, repeated enough times with proper bankroll management, the bet will profit on average. EV is the single most important concept in sports betting because it separates skill from luck: short sequences of results are dominated by variance, but EV determines the direction of the long run. A bet can lose nine times out of ten and still have been the correct decision if its EV was positive. Calibrated probability models are the only practical way to estimate p reliably, and margin-adjusted bookmaker odds are the benchmark to beat. Minimum actionable edge for most professional bettors is 3–5 percent EV after accounting for model uncertainty and execution friction.',
    related: ['value-bet', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'implied-probability',
    term: 'Implied probability',
    shortDefinition:
      'The probability baked into a bookmaker’s odds, equal to 1 / decimal_odds before margin removal.',
    body:
      'Implied probability is the probability that a bookmaker’s decimal odds suggest for an outcome, computed as 1 / decimal_odds. Raw 1X2 implied probabilities sum to more than 100 percent — typically 104–108 percent — because bookmakers build in a margin, also called the overround or vig. To compare market probability fairly with a model, the three raw implied probabilities must be normalised by dividing each by their sum, so they total exactly 1.0. Only normalised implied probabilities represent the bookmaker’s honest view. The difference between the bookmaker’s raw and normalised numbers is exactly the house edge on that market. Implied probability is not the same as true probability: it is the market’s estimate net of margin, and finding value bets is mathematically equivalent to finding matches where your calibrated model disagrees with the normalised implied probability by a statistically meaningful amount.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'kelly-criterion',
    term: 'Kelly criterion',
    shortDefinition:
      'A formula for stake size that maximises the long-run geometric growth of a bankroll given a known edge.',
    body:
      'The Kelly criterion is a staking formula developed by John Kelly in 1956 that maximises the geometric growth rate of a bankroll. For a decimal-odds bet the formula is f = (p × odds − 1) / (odds − 1), where p is the true probability of winning and f is the fraction of bankroll to stake. Full Kelly is optimal only when probabilities are known exactly; in practice, model uncertainty means full Kelly stakes are too volatile and expose the bettor to severe drawdowns on a bad sequence. Most professional bettors therefore use fractional Kelly — typically 25–50 percent of the full Kelly stake — which preserves most of the long-run growth while cutting drawdown risk in half. Kelly sizing gives zero stake to any bet with non-positive EV, which is the correct behaviour: betting on negative-EV outcomes destroys a bankroll even if the probabilities are right.',
    termCode: 'Kelly',
    related: ['expected-value', 'value-bet', 'bankroll'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'pi-rating',
    term: 'Pi-rating',
    shortDefinition:
      'A football-specific strength rating, an Elo successor with separate home and away ratings per team.',
    body:
      'Pi-ratings are a football-specific strength-rating system proposed by Constantinou and Fenton (2013) as a successor to Elo. Each team has two numeric ratings — home and away — updated after each match with a non-linear function of the goal difference, capped to reduce the influence of blowouts. The key innovations over Elo are the explicit home/away split, which accurately captures venue effects without a blanket home-advantage constant, and the non-linear goal-difference update, which converges faster after promotions and relegations. Empirically, Pi-ratings achieve a lower Brier score than Elo on out-of-sample football matches and serve as a strong baseline predictor in their own right. In production models they are usually combined with features such as recent form, lineups and expected goals to boost accuracy further, but a naive pi-rating model already beats the implied probability of bookmaker odds on some second-tier leagues.',
    related: ['elo-rating', 'expected-goals'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'catboost',
    term: 'CatBoost',
    shortDefinition:
      'A gradient-boosting decision-tree library optimised for categorical features and ordered boosting.',
    body:
      'CatBoost is a gradient-boosting decision-tree library released by Yandex in 2017. It differs from XGBoost and LightGBM in two practically important ways: native handling of categorical features without one-hot encoding, and ordered boosting, which reduces target leakage during training. Both advantages matter for football prediction, where team identity, referee, stadium and kickoff day-of-week are high-cardinality categorical features that are hard to one-hot without losing signal. Empirically, CatBoost outperforms XGBoost by roughly 0.003 ranked-probability-score points on 1X2 football predictions with no hyper-parameter tuning and matches or exceeds deep neural baselines on the same data with far shorter training time. Its calibration out-of-the-box is better than most GBM libraries, though production systems still benefit from isotonic or Platt recalibration to squeeze the remaining expected calibration error below 1.5 percent.',
    related: ['expected-value', 'calibration'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'calibration',
    term: 'Probability calibration',
    shortDefinition:
      'The property that stated probabilities match observed outcome frequencies over many predictions.',
    body:
      'A probability estimate is well calibrated when the fraction of positives among predictions with stated probability p is equal to p, over many samples. A model that says 70 percent ten thousand times should be right roughly 7 000 times. Calibration is a separate quality from discrimination: a model can sort winners from losers correctly yet still quote the wrong absolute probabilities, and such a model is useless for betting because expected-value calculations require correct probabilities, not rankings. The Expected Calibration Error (ECE) is the most common scalar measure; production betting models target ECE below 1.5 percent. Two standard techniques achieve this in practice: isotonic regression, a non-parametric monotonic mapping from raw scores to calibrated probabilities, and Platt scaling, a two-parameter sigmoid fit. Both require a held-out calibration set distinct from training data to avoid over-fitting.',
    related: ['catboost', 'expected-value', 'brier-score'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'closing-line-value',
    term: 'Closing line value (CLV)',
    shortDefinition:
      'The difference between the odds at which a bet was placed and the closing odds at kick-off.',
    termCode: 'CLV',
    body:
      'Closing line value (CLV) measures whether a bettor is getting a better price than the market settles at by kick-off. If you bet at 2.00 and the closing odds are 1.90, you have +CLV; the market has moved against your side, which is strong evidence that you identified an edge before sharper bettors arrived. CLV is widely considered the best leading indicator of long-run betting profit because closing odds are the most efficient price the market produces, incorporating all public information right before the match. Positive average CLV over a large sample almost always implies positive expected ROI, even if short-term results are negative due to variance. Bookmakers track CLV per customer and limit or close accounts that consistently beat the closing line. Transparent performance trackers therefore report rolling CLV alongside raw ROI.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'btts',
    term: 'Both teams to score (BTTS)',
    shortDefinition:
      'A football market that settles Yes if both sides score at least one goal and No otherwise.',
    termCode: 'BTTS',
    body:
      'Both teams to score (BTTS) is a binary football market that settles Yes when both teams score at least one goal during regulation time and No otherwise. It is popular because a single late goal can convert a losing ticket, making it perceive as higher-engagement than 1X2. From a modelling perspective BTTS is derived from the joint distribution of home and away goals: under a Dixon-Coles bivariate Poisson model, P(BTTS=Yes) = 1 − P(HG=0) − P(AG=0) + P(HG=0, AG=0) where HG and AG are home and away goals. League-level BTTS base rates typically sit between 48 and 58 percent, so markets are more balanced than 1X2 and margins are somewhat tighter. Value tends to appear in matches where one team is missing its main striker or the weather forecast points to a low-scoring game.',
    related: ['over-under-2-5', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'over-under-2-5',
    term: 'Over/Under 2.5 goals',
    shortDefinition:
      'A football market that settles Over if three or more goals are scored and Under if two or fewer.',
    body:
      'Over/Under 2.5 goals is the most traded football goals market worldwide. It settles Over when three or more goals are scored in regulation time and Under when two or fewer are scored; the half-goal cut avoids push outcomes. Like BTTS, it is derived from the joint goal distribution: with a Dixon-Coles Poisson model you compute P(Over 2.5) = 1 − P(total goals ≤ 2). League base rates vary from around 47 percent in defensive leagues to 58 percent in high-scoring leagues such as the Bundesliga. Because the market is driven primarily by league-level scoring rates and match-specific expected-goals, a well-tuned goals model can often find more consistent value here than in 1X2. Weather, confirmed lineups and referee leniency are meaningful features for this market.',
    related: ['btts', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
];

export const GLOSSARY_SLUGS: readonly string[] = GLOSSARY_ENTRIES.map(
  (e) => e.slug,
);

export function getGlossaryEntry(slug: string): GlossaryEntry | undefined {
  return GLOSSARY_ENTRIES.find((e) => e.slug === slug);
}
