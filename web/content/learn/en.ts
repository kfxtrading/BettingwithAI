import type { LearnArticle } from './types';

const LAST_UPDATED = '2026-04-01';

const articles: Record<string, LearnArticle> = {
  'value-bets': {
    slug: 'value-bets',
    title: 'Value Bets in Football: What They Are and How to Find Them',
    description:
      'A value bet is a wager whose true probability of winning exceeds the implied probability of the bookmaker’s odds. Here is how to spot one — with worked examples.',
    tldr:
      'A value bet exists when your estimated probability of an outcome is higher than the bookmaker’s implied probability after removing the margin. The expected value is positive even if the bet loses on any given day.',
    sections: [
      {
        heading: 'Definition',
        paragraphs: [
          'A value bet is any bet where (your estimated probability) × (decimal odds) > 1. The product is also called expected value (EV). Positive EV is the only thing that matters in the long run; the result of any single match is noise.',
          'The market’s implied probability is 1 / decimal_odds, but raw 1X2 odds bake in a 4–8% bookmaker margin. You must remove that margin first to compare apples with apples.',
        ],
      },
      {
        heading: 'How to find value bets',
        paragraphs: [
          'Build or use a model that outputs calibrated probabilities for Home, Draw and Away. Convert all three bookmaker odds to implied probabilities, divide each by their sum so they total 1.0, and compare to your model. Any outcome where model probability exceeds market probability by 2–3+ percentage points is a candidate value bet.',
          'Stake size matters as much as edge detection. Fractional Kelly (typically 25–50% of full Kelly) maximises long-term geometric growth without ruining you on a bad week.',
        ],
      },
      {
        heading: 'Why most "tips" are not value bets',
        paragraphs: [
          'Affiliate-driven prediction sites pick the most likely outcome, not the most mispriced one. Picking favourites has nothing to do with finding value — a 1.20 favourite with 90% true probability is a 1.08 EV; a 4.50 underdog with 25% true probability is a 1.125 EV. The underdog is the value bet.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Are value bets a guarantee of profit?',
        answer:
          'No. Value bets are positive in expectation, not in any single match. Variance can be brutal over 100 bets and meaningful only over hundreds.',
      },
      {
        question: 'How big does an edge need to be to bet?',
        answer:
          'Most professional bettors require ≥ 3–5% edge after model uncertainty and the bookmaker margin to overcome variance and execution costs.',
      },
      {
        question: 'Why does the bookmaker offer value bets at all?',
        answer:
          'Bookmakers price for the median customer. Soft books in particular are slow to update on injuries, lineup news and sharp money — that lag is where value lives.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-01',
  },

  'implied-probability': {
    slug: 'implied-probability',
    title: 'Implied Probability from Odds: Formula and Margin Removal',
    description:
      'Convert decimal, fractional and American odds into implied probabilities — and learn how to strip the bookmaker margin so the three outcomes sum to 100%.',
    tldr:
      'Implied probability = 1 / decimal_odds. Because the three 1X2 implied probabilities sum to >100% (the overround), divide each by the total to get the margin-free probability.',
    sections: [
      {
        heading: 'The formula',
        paragraphs: [
          'For decimal odds: implied = 1 / odds. So odds of 2.00 imply 50%, odds of 4.00 imply 25%.',
          'For fractional odds (e.g. 5/2): implied = denominator / (numerator + denominator) = 2/7 ≈ 28.6%.',
          'For American odds: positive (+150) → 100/(150+100) = 40%; negative (-200) → 200/(200+100) = 66.7%.',
        ],
      },
      {
        heading: 'Removing the margin',
        paragraphs: [
          'Sum the three 1X2 implied probabilities. If they sum to 1.06, the overround is 6%. Divide each implied probability by 1.06 to get the bookmaker’s "true" estimate. This is the number you compare to your model.',
          'For two-way markets like Over/Under, the same logic applies — divide by the sum of the two implied probabilities.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Is the margin always evenly distributed?',
        answer:
          'No. Bookmakers shade the margin onto favourites or longshots depending on customer bias. Proportional removal is a simple approximation; better methods include the Shin and power methods.',
      },
      {
        question: 'Why does my margin-free probability feel low?',
        answer:
          'Because raw odds always overstate the bookmaker’s confidence by the margin. Margin removal reveals the genuine market estimate.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'kelly-criterion': {
    slug: 'kelly-criterion',
    title: 'Kelly Criterion for Sports Betting: The Complete Guide (2026)',
    description:
      'A long-form guide to the Kelly criterion in football betting: derivation, formula, worked examples, fractional Kelly, multi-bet Kelly, drawdown analysis and an interactive calculator.',
    tldr:
      'Kelly stake = (bp − q) / b, where b is decimal_odds − 1, p is your win probability and q is 1 − p. Full Kelly maximises long-term geometric growth of bankroll — but most pros use a quarter or half of that to control variance and tolerate model error.',
    sections: [
      {
        heading: 'Why Kelly exists: maximising geometric growth',
        paragraphs: [
          'The Kelly criterion was published by John L. Kelly Jr. at Bell Labs in 1956. It answers a precise question: what fraction of your bankroll should you stake on a positive-EV bet to maximise the long-run geometric growth rate of wealth?',
          'The geometric mean — not the arithmetic mean — is the right objective for repeated bets, because it is what compounds. A strategy that doubles in good years and halves in bad ones has an arithmetic mean of +25% and a geometric mean of 0%.',
          'Kelly therefore is not about being aggressive or cautious; it is the unique stake size that maximises log-utility. Stake more than Kelly and you reduce growth; stake less and you also reduce growth (but you also reduce volatility).',
        ],
      },
      {
        heading: 'The formula',
        paragraphs: [
          'For a single binary bet at decimal odds o with your estimated win probability p:',
          'f* = (b·p − q) / b, where b = o − 1 and q = 1 − p.',
          'f* is the fraction of bankroll to stake. If f* ≤ 0, Kelly says do not bet — the bet has zero or negative expected value.',
          'Equivalent form: f* = p − q/b = p − (1 − p)/(o − 1). Useful for spreadsheets.',
        ],
      },
      {
        heading: 'Worked football example',
        paragraphs: [
          'Manchester City vs Arsenal, decimal odds 2.10 on City. Your model gives City a 55% win probability.',
          'b = 2.10 − 1 = 1.10. q = 1 − 0.55 = 0.45. f* = (1.10 × 0.55 − 0.45) / 1.10 = (0.605 − 0.45) / 1.10 = 0.155 / 1.10 ≈ 14.1%.',
          'Full Kelly says stake 14.1% of bankroll. With a £1,000 bankroll that is £141 — uncomfortably large for most retail bettors. This is why fractional Kelly exists.',
        ],
      },
      {
        heading: 'Fractional Kelly: why pros stake a fraction of f*',
        paragraphs: [
          'Full Kelly assumes you know p exactly. In reality your model has error: a calibrated model still has a few percentage points of noise on any single match. If your stated p is 0.55 and the truth is 0.51, Kelly with the wrong p produces sharply higher drawdowns.',
          'Half-Kelly stakes 50% of f*. It captures roughly 75% of the long-run growth with about 50% of the volatility — a near-universally winning trade-off in sports betting.',
          'Quarter-Kelly stakes 25% of f*. Industry-standard for quants who treat their probabilities as approximate. Drawdowns drop to about 25% of full Kelly.',
          'A useful rule of thumb: stake k × f* where k = (your trust in p). If you are 80% confident in your calibration, k ≈ 0.5 is reasonable.',
        ],
      },
      {
        heading: 'Drawdown intuition',
        paragraphs: [
          'For an unbiased Kelly bettor, the probability of ever drawing down more than x% of starting bankroll is approximately x. Full Kelly therefore implies a 30% chance of a 30% drawdown at some point — even though the strategy has positive long-term EV.',
          'Half-Kelly compresses that to about a 15% chance of a 30% drawdown. Quarter-Kelly compresses it further. The maths punishes overconfidence.',
        ],
      },
      {
        heading: 'Multi-bet Kelly: betting several matches at once',
        paragraphs: [
          'When you have several positive-EV bets on the same day, single-bet Kelly will over-allocate if you sum the stakes naively. Two simultaneous bets at f* = 10% each cannot together stake 20% — they would correlate poorly with bankroll constraints.',
          'Practical fix: solve a small constrained optimisation that maximises expected log-bankroll subject to f_total ≤ K (typically 25–30%). For independent bets this reduces nicely to per-bet Kelly capped by a portfolio budget.',
          'For correlated bets (same match, e.g. 1X2 and Over/Under) the joint optimisation matters more — covariance pulls down each Kelly stake.',
        ],
      },
      {
        heading: 'Practical rules every Kelly bettor should follow',
        paragraphs: [
          '1. Cap any single stake at 1–3% of bankroll regardless of f*. Variance does not care about your formula.',
          '2. Refuse f* < 0 entirely — never bet a negative-EV market just because it is a "lock".',
          '3. Re-evaluate bankroll monthly, not per-bet. Up-staking after a winning streak is the classic variance trap.',
          '4. Pair Kelly with a stop-loss (-25% triggers a model review) and a stop-win (lock 50% of profits at +50%).',
          '5. Track every bet — without a log there is no edge.',
        ],
      },
    ],
    faqs: [
      {
        question: 'What if Kelly says zero or negative?',
        answer:
          'Do not bet. A negative Kelly value means the bet has negative expected value at the odds offered.',
      },
      {
        question: 'Can I use Kelly with parlays?',
        answer:
          'Technically yes, but parlay variance is so high that Kelly stakes are tiny. Most quants avoid parlays except for hedging — the bookmaker margin compounds across legs.',
      },
      {
        question: 'How do I size if I bet on multiple matches at once?',
        answer:
          'Use simultaneous Kelly: solve a small optimisation that sizes each bet jointly subject to a total-stake constraint. Or apply per-bet Kelly and cap total exposure at 25–30% of bankroll.',
      },
      {
        question: 'Is half-Kelly always better than full-Kelly?',
        answer:
          'For real bettors with imperfect probabilities, almost always yes. The classical theorem assumes p is known exactly. Once you allow estimation error, half-Kelly dominates full-Kelly on risk-adjusted returns for any plausible noise level.',
      },
      {
        question: 'Where can I try this on my own numbers?',
        answer:
          'We provide a free interactive Kelly calculator with full and fractional Kelly, multi-bet portfolio mode and decimal/American/fractional odds conversion at /tools/kelly-calculator.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

  'bankroll-management': {
    slug: 'bankroll-management',
    title: 'Bankroll Management for Football Betting: A Practical Guide',
    description:
      'Bankroll management is the discipline of sizing your bets so you survive variance long enough for your edge to play out. Here are the rules that actually work.',
    tldr:
      'Treat your bankroll as a separate, fixed pool. Risk 0.5–2% per bet, never chase losses, and re-evaluate stakes monthly — not after every win or loss.',
    sections: [
      {
        heading: 'The five rules',
        paragraphs: [
          '1. Use only money you can lose. Never use rent, savings or borrowed funds.',
          '2. Risk 1% of bankroll per bet by default; use Kelly fractional sizing only if you know your probabilities are calibrated.',
          '3. Track every bet (date, market, odds, stake, result, model probability). Without a log there is no edge.',
          '4. Re-stake monthly, not daily. Up-staking after a hot week is a classic variance trap.',
          '5. Set a stop-loss (e.g. -25% of bankroll triggers a model review) and a stop-win (lock half profits at +50%).',
        ],
      },
    ],
    faqs: [
      {
        question: 'How big should a starting bankroll be?',
        answer:
          'Whatever amount you can lose without lifestyle impact. Many serious recreational bettors start with 100× their typical stake.',
      },
      {
        question: 'Should I withdraw profits?',
        answer:
          'Yes, periodically. Realised profits never go back. Many bettors auto-withdraw 50% of every monthly gain.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'closing-line-value': {
    slug: 'closing-line-value',
    title: 'Closing Line Value (CLV): The Best Predictor of Long-Term ROI',
    description:
      'CLV measures how much better the odds you took were than the odds at kick-off. It is the single best leading indicator of profitability.',
    tldr:
      'Closing Line Value (CLV) = (your_odds / closing_odds) − 1. Consistently positive CLV is statistical proof of an edge, even before results are settled.',
    sections: [
      {
        heading: 'Why CLV matters more than ROI in the short run',
        paragraphs: [
          'ROI over 50 bets is mostly noise. CLV converges much faster: 200 bets are usually enough to confirm a +2% mean CLV is real, while 200 bets of ROI prove almost nothing.',
          'Sharps and modellers are judged on CLV in their first 6–12 months. If CLV is positive, the bankroll will follow.',
        ],
      },
      {
        heading: 'How to measure it',
        paragraphs: [
          'Record the closing 1X2 odds at kick-off (Pinnacle’s closing line is the gold standard) and compare to the odds you actually took. Your CLV is positive if your odds were higher.',
          'Aggregate the mean CLV per bet. Even +1.5% mean CLV after the bookmaker margin signals a profitable strategy at sharp books.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Where can I get reliable closing odds?',
        answer:
          'Pinnacle is the de facto reference market. Public archives like oddsportal.com and the football-data.co.uk historic CSVs include closing odds for thousands of past fixtures.',
      },
      {
        question: 'Can a bet have positive CLV and still lose?',
        answer:
          'Of course — CLV measures pricing skill, not luck. Over hundreds of bets, positive CLV translates to positive ROI; on any single match, the result is noise.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'expected-goals-xg': {
    slug: 'expected-goals-xg',
    title: 'Expected Goals (xG) Explained: How It Works and What It Predicts',
    description:
      'Expected goals (xG) assigns each shot a probability of becoming a goal based on its location, type and context. Here is what xG measures, what it does not, and how to use it for betting.',
    tldr:
      'xG is the sum of per-shot scoring probabilities. Over a season, team xG is far more predictive of future results than goals scored — variance dominates short samples.',
    sections: [
      {
        heading: 'What an xG model uses',
        paragraphs: [
          'Each shot is scored with features like distance to goal, angle, body part, assist type (through-ball vs cross), defensive pressure and game state. The model outputs a 0–1 probability per shot.',
          'A team’s xG for a match is the sum of those per-shot probabilities. Over 38 matches, a Premier League side that out-xG’s the league by +0.5 per game is virtually certain to finish top six.',
        ],
      },
      {
        heading: 'How to use xG in match prediction',
        paragraphs: [
          'Rolling 5–10 match xG-for and xG-against are stronger features than goal differential because they remove finishing variance and goalkeeper hot streaks.',
          'Combine xG with shot quality (xG-per-shot) to detect teams generating chances differently — chance-quality teams are more sustainable than chance-quantity teams.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Is xG better than goals?',
        answer:
          'For predicting future matches, almost always yes. For describing what happened, goals win — only goals affect the league table.',
      },
      {
        question: 'Why do xG models disagree?',
        answer:
          'Different vendors use different feature sets and training data. Use one model consistently; the absolute values matter less than relative comparisons within the same model.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'btts-explained': {
    slug: 'btts-explained',
    title: 'Both Teams To Score (BTTS): Strategy, Odds and Common Mistakes',
    description:
      'BTTS pays if both sides score at least one goal. Learn how it is priced, when the market mispriceses it and what to look for in team profiles.',
    tldr:
      'BTTS Yes is profitable when two attacking teams with leaky defences meet — typical odds are 1.65–1.90. Pure xG is a strong predictor; team-level finishing variance is not.',
    sections: [
      {
        heading: 'When BTTS Yes has value',
        paragraphs: [
          'Look for two sides that each generate ≥ 1.3 xG-for and concede ≥ 1.0 xG-against per game over the last 10 matches. Mid-table to attacking-mid sides historically over-deliver on BTTS.',
          'Avoid BTTS Yes in matches involving elite defensive sides with strong goalkeepers — they post too many clean sheets to support the price.',
        ],
      },
      {
        heading: 'BTTS No: the contrarian play',
        paragraphs: [
          'BTTS No is undervalued in matchups featuring a heavy favourite + a defensively weak underdog: the favourite often wins to nil. League averages help: Serie A historically has higher BTTS No rates than the Bundesliga.',
        ],
      },
    ],
    faqs: [
      {
        question: 'What does "BTTS Yes & Over 2.5" mean?',
        answer:
          'A combined market: both teams must score AND the total goals must be 3 or more. It is a more demanding condition with longer odds.',
      },
      {
        question: 'Is BTTS easier to predict than 1X2?',
        answer:
          'It is a binary outcome, so calibration is simpler. But the bookmaker margin on BTTS is often higher than on 1X2 — so the edge per bet is usually smaller.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'over-under-2-5': {
    slug: 'over-under-2-5',
    title: 'Over/Under 2.5 Goals: How the Market Works and How to Beat It',
    description:
      'Over 2.5 pays if 3+ goals are scored. Here is how to predict goal totals using xG, league context and tempo signals.',
    tldr:
      'Over/Under 2.5 is settled at the 3-goal threshold. Predict it from combined team xG, opponent xG-against, league average goals-per-game and venue effects.',
    sections: [
      {
        heading: 'Modelling goal totals',
        paragraphs: [
          'A simple Poisson model uses each side’s expected goals_for + opponent goals_against, adjusted for league average. Combined expected goals of ≥ 2.7 typically support an Over 2.5 lean at fair odds.',
          'Dixon-Coles refines Poisson by correcting low-score correlations (0-0, 1-0, 0-1, 1-1) — the standard adjustment in football modelling since 1997.',
        ],
      },
      {
        heading: 'Common mistakes',
        paragraphs: [
          'Recency bias is the killer. A 4-0 thrashing in the last fixture pushes casual bettors to Over; the model should not move much because expected goals barely changed.',
          'Ignoring weather and pitch conditions in winter — a heavy pitch or strong wind reliably lowers the goal ceiling.',
        ],
      },
    ],
    faqs: [
      {
        question: 'What is the long-term Over 2.5 hit rate?',
        answer:
          'Across the Top 5 leagues it sits around 53–55%. With typical Over 2.5 odds at 1.85, breakeven needs 54.1% — so it is a tight market.',
      },
      {
        question: 'What is Over 2.5 Asian Handicap?',
        answer:
          'Asian total goal markets push the line by 0.25 or 0.5 to remove pushes. Over 2.75, for example, splits stake between Over 2.5 and Over 3.0.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  '1x2-explained': {
    slug: '1x2-explained',
    title: '1X2 Betting Explained: The Most Liquid Football Market',
    description:
      '1X2 is a three-way bet on Home win (1), Draw (X) or Away win (2). Here is how it is priced, why margins differ and how to find value.',
    tldr:
      '1X2 is the deepest, most-liquid football market. The three implied probabilities sum to 104–108% — the overround. Removing it gives the market’s true probability estimate.',
    sections: [
      {
        heading: 'How the market is priced',
        paragraphs: [
          'Sharp books like Pinnacle price 1X2 to 100.5–101% (sub-2% margin). Recreational books carry 5–8% margin. Always price-shop multiple books before placing.',
          'Draws are systematically harder to predict than wins — implied draw probability typically ranges 22–28% with a tight band, so most edges come from H or A side.',
        ],
      },
      {
        heading: 'Where 1X2 value lives',
        paragraphs: [
          'Market overreaction to recent results (4-0 wins, derby losses) on small-sample teams. Models that ignore short-term noise consistently beat human-set lines on these matches.',
          'Late-season dead-rubbers where one side has nothing to play for — public money over-rewards the still-motivated side.',
        ],
      },
    ],
    faqs: [
      {
        question: 'What is "1N2" in French betting sites?',
        answer:
          'Identical to 1X2: 1 = Home win, N = Nul (Draw), 2 = Away win. The notation differs by language only.',
      },
      {
        question: 'Should I bet the draw?',
        answer:
          'Only when you have a calibrated probability above the implied. Draws are coin-flip-like in close matches; many models simply pass on them.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'model-accuracy-brier-calibration': {
    slug: 'model-accuracy-brier-calibration',
    title: 'How to Judge a Football Prediction Model: Brier, RPS and Calibration',
    description:
      'Hit rate is a poor metric for probabilistic models. Brier score, RPS and reliability diagrams reveal whether a model is genuinely calibrated.',
    tldr:
      'Use Brier score and Ranked Probability Score (RPS) to compare probabilistic models, and a reliability diagram to verify that, say, "70%-confidence" picks actually win 70% of the time.',
    sections: [
      {
        heading: 'Why hit rate is misleading',
        paragraphs: [
          'A model that always picks the favourite scores ~52% hit rate in the Premier League — but provides zero edge over the bookmaker. Hit rate ignores whether probabilities are right; it only checks the argmax.',
        ],
      },
      {
        heading: 'Brier score and RPS',
        paragraphs: [
          'Brier = mean squared error between predicted probability vector and one-hot actual outcome. Lower is better.',
          'RPS (Ranked Probability Score) is Brier’s ordinal cousin: it penalises confident wrong predictions on adjacent outcomes (Home / Draw / Away) less than confident wrong predictions on opposite outcomes. RPS is the gold-standard 1X2 metric.',
        ],
      },
      {
        heading: 'Calibration in plain English',
        paragraphs: [
          'Bin all predictions by predicted probability (0–10%, 10–20%, …). For each bin, compute the actual hit rate. Plot predicted_mean vs actual_rate. A perfectly calibrated model sits on the diagonal.',
          'Expected Calibration Error (ECE) is the average distance from the diagonal weighted by bin size. ECE < 1.5% after isotonic post-calibration is the bar serious modellers aim for.',
        ],
      },
    ],
    faqs: [
      {
        question: 'How many predictions do I need to evaluate calibration?',
        answer:
          'A few hundred per league at minimum. With < 200 predictions, the bins are too sparse to draw conclusions.',
      },
      {
        question: 'Is hit rate ever useful?',
        answer:
          'As a sanity check, yes. As the headline metric for a probabilistic model, no — a model with worse hit rate but better calibration is the more profitable model.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'catboost-vs-xgboost': {
    slug: 'catboost-vs-xgboost',
    title: 'CatBoost vs XGBoost for Football Prediction: A Practitioner Comparison',
    description:
      'A side-by-side comparison of CatBoost and XGBoost for 1X2 football prediction — categorical handling, training speed, calibration, RPS, and when to choose which.',
    tldr:
      'Both libraries reach near-identical predictive accuracy on football tabular data. CatBoost wins on out-of-the-box categorical handling and calibration; XGBoost wins on raw training speed on dense numerical features and ecosystem maturity. For 1X2 with 70+ mixed features, CatBoost is the safer default.',
    sections: [
      {
        heading: 'Why this comparison matters',
        paragraphs: [
          'CatBoost (Yandex, 2017) and XGBoost (Tianqi Chen, 2014) dominate gradient-boosted decision tree work on tabular data. Football match prediction with engineered features (Pi-Ratings, rolling xG, rest days, league-encoded categoricals) is firmly in the tabular regime where both shine.',
          'They differ enough in their tree-construction strategy, categorical handling and regularisation that the right choice can move RPS by 0.3–0.6 percentage points on a held-out season. Over a betting career, that is real money.',
        ],
      },
      {
        heading: 'How they differ under the hood',
        paragraphs: [
          'XGBoost uses level-wise tree growth with second-order gradient boosting and elaborate regularisation (L1, L2, min-child-weight). It treats every feature as numeric — categoricals must be one-hot, label-encoded or target-encoded by you.',
          'CatBoost uses oblivious trees (the same split is applied at every node of a level), which act as a structural regulariser, and an ordered boosting scheme that prevents target leakage when target-encoding categoricals automatically.',
          'In practice CatBoost is more robust to default hyper-parameters; XGBoost is faster and more tunable, but punishes you harder for sloppy categorical encoding.',
        ],
      },
      {
        heading: 'Empirical comparison on 1X2 football data',
        paragraphs: [
          'On our Top 5 leagues feature set (70+ features, 5 seasons of training, walk-forward backtest), CatBoost and XGBoost finish within 0.005 RPS of each other when both are properly tuned. Default hyper-parameters favour CatBoost by ~0.01 RPS.',
          'Calibration is where CatBoost has a meaningful lead: ECE before isotonic post-calibration is roughly 2.4% (CatBoost) vs 3.1% (XGBoost). After isotonic, both drop below 1.5% — but CatBoost needs less correction.',
          'Training speed on a 16-core CPU: XGBoost trains the same model in ~60% of the time of CatBoost. On a single GPU the gap closes; CatBoost has a particularly fast GPU mode.',
        ],
      },
      {
        heading: 'When to choose CatBoost',
        paragraphs: [
          'Many high-cardinality categorical features (team IDs, referee IDs, venues). CatBoost target-encodes them safely without leakage.',
          'You want strong out-of-the-box calibration and limited time to tune. Defaults are forgiving.',
          'Your dataset has missing values you do not want to impute manually.',
        ],
      },
      {
        heading: 'When to choose XGBoost',
        paragraphs: [
          'Your features are mostly dense numerical and you have already encoded categoricals carefully.',
          'You need the absolute fastest training time on CPU.',
          'You are integrating with an ecosystem (e.g. SHAP, MLflow, ONNX, Spark) where XGBoost is a first-class citizen.',
        ],
      },
      {
        heading: 'Practical hyper-parameter starting points (1X2)',
        paragraphs: [
          'CatBoost: iterations=1500, learning_rate=0.05, depth=6, l2_leaf_reg=3.0, loss_function="MultiClass", auto_class_weights="Balanced".',
          'XGBoost: n_estimators=2000, learning_rate=0.05, max_depth=5, subsample=0.85, colsample_bytree=0.85, objective="multi:softprob", eval_metric="mlogloss".',
          'Always evaluate with RPS, log-loss and ECE — never with raw accuracy.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Should I use LightGBM instead?',
        answer:
          'LightGBM is competitive and faster than XGBoost on large datasets. For < 1M rows of football data, the speed gap is rarely material; calibration is the bigger differentiator and CatBoost still wins there.',
      },
      {
        question: 'Do I need to one-hot encode for XGBoost?',
        answer:
          'Recent XGBoost versions support categorical splits natively (enable_categorical=True) since 1.6. It is improving but still less robust than CatBoost defaults — handle high-cardinality columns explicitly.',
      },
      {
        question: 'Will an ensemble of both beat either alone?',
        answer:
          'Yes, marginally. A 50/50 average of calibrated CatBoost and XGBoost probabilities typically reduces RPS by another 0.001–0.003 versus the best single model. Diminishing returns set in fast.',
      },
      {
        question: 'Which one does Betting with AI use?',
        answer:
          'CatBoost, ensembled with a Dixon-Coles Poisson goal model and a PyTorch MLP. See our /methodology page for the full architecture.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

  'pi-ratings-explained': {
    slug: 'pi-ratings-explained',
    title: 'Pi-Ratings Explained: The Football Rating System Behind Modern Models',
    description:
      'Pi-Ratings (Constantinou & Fenton, 2013) are the venue-aware football rating system used in many modern prediction models. This guide derives the update rule, runs a worked example and shows how to use Pi-Ratings as model features.',
    tldr:
      'Pi-Ratings give every team a separate home and away strength updated after each match by a weighted error term. They beat raw league position and Elo on out-of-sample 1X2 prediction by 1–2% accuracy at zero implementation cost.',
    sections: [
      {
        heading: 'What Pi-Ratings are',
        paragraphs: [
          'Pi-Ratings, introduced by Anthony Costa Constantinou and Norman E. Fenton in their 2013 paper "Determining the Level of Ability of Football Teams by Dynamic Ratings Based on the Relative Discrepancies in Scores Between Adversaries", assign each team two ratings: a home rating R_H and an away rating R_A.',
          'The two-rating split is what makes Pi-Ratings particularly suited to football. Home advantage is large (≈ 0.3 goals across the Top 5 leagues) and team-specific — Atalanta have historically been a noticeably stronger home side than away side; Brighton the opposite.',
          'Compared to a single-rating Elo, Pi-Ratings reduce out-of-sample log-loss by 2–4% on 1X2 prediction in published benchmarks — a real edge.',
        ],
      },
      {
        heading: 'The update rule',
        paragraphs: [
          'Before kick-off the predicted goal difference between home team H and away team A is gd_pred = R_H(home) − R_A(away).',
          'After the match with actual goal difference gd_actual, the error is e = gd_actual − gd_pred. The "diminishing returns" function ψ(e) = sign(e) · 3 · log10(1 + |e|) prevents large blowouts from dominating.',
          'Both teams update both their ratings, with separate learning rates λ for the venue side that just played and γ for the opposite venue side (typical values: λ ≈ 0.06, γ ≈ 0.5·λ).',
          'Home team:  R_H(home) ← R_H(home) + λ · ψ(e);  R_H(away) ← R_H(away) + γ · ψ(e).',
          'Away team:  R_A(away) ← R_A(away) − λ · ψ(e);  R_A(home) ← R_A(home) − γ · ψ(e).',
        ],
      },
      {
        heading: 'Worked example',
        paragraphs: [
          'Bayern (R_H_home = 1.20, R_H_away = 0.40) host Leipzig (R_A_home = 0.80, R_A_away = 0.20). Predicted goal difference = 1.20 − 0.20 = +1.00.',
          'Bayern win 3-1, so e = 2 − 1 = +1. ψ(1) = 3·log10(2) ≈ 0.903. With λ = 0.06 and γ = 0.03:',
          'Bayern home rating ← 1.20 + 0.06·0.903 ≈ 1.254. Bayern away rating ← 0.40 + 0.03·0.903 ≈ 0.427.',
          'Leipzig away rating ← 0.20 − 0.06·0.903 ≈ 0.146. Leipzig home rating ← 0.80 − 0.03·0.903 ≈ 0.773.',
        ],
      },
      {
        heading: 'Using Pi-Ratings as model features',
        paragraphs: [
          'Direct features: R_H_home, R_H_away, R_A_home, R_A_away, plus their deltas and the predicted goal difference. These five derived features alone reach ~52–54% accuracy on 1X2 — close to a baseline market-following model.',
          'Better: feed them into a Poisson model. Translate R_diff = R_H(home) − R_A(away) into expected home and away goals via a learned linear map, then convert to 1X2 with the Skellam distribution. This is the canonical "Pi-Poisson" hybrid.',
          'Even better: include them as features in a CatBoost / XGBoost / MLP ensemble alongside xG, rest days and form. Pi-Ratings then act as a strong prior that shrinks model error on small samples.',
        ],
      },
      {
        heading: 'Common pitfalls',
        paragraphs: [
          'Cold-start: new promoted teams have no rating history. Initialise with the league-mean rating minus a relegation discount (≈ −0.3), and let the first 5–8 fixtures recalibrate them.',
          'Cup matches: keep cup ratings separate or use a smaller learning rate. Cup form is noisier than league form and can pollute league predictions.',
          'Mid-season transfers: Pi-Ratings adapt slowly. After a marquee signing or coach change, manually inject a small bump (±0.1) or temporarily raise λ for that team.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Are Pi-Ratings better than Elo for football?',
        answer:
          'Yes, slightly. The home/away split captures venue-specific strength that pure-Elo cannot. Both are dominated by full feature-based ML models, but Pi-Ratings remain a top-3 single feature in any 1X2 model.',
      },
      {
        question: 'What learning rate should I use?',
        answer:
          'The original paper used λ ≈ 0.06 and γ = 0.5·λ. We recommend grid-searching λ ∈ {0.04, 0.05, 0.06, 0.07, 0.08} on a hold-out season, optimising RPS or log-loss.',
      },
      {
        question: 'Can Pi-Ratings predict goal totals (Over/Under)?',
        answer:
          'Indirectly. The rating difference predicts goal difference, not total goals. Pair Pi-Ratings with a Poisson model whose intercepts are league-tuned and you get strong Over/Under and BTTS predictions.',
      },
      {
        question: 'Where can I see Pi-Ratings used in practice?',
        answer:
          'Betting with AI uses them as one of three core inputs to its 1X2 ensemble. See /methodology for the full architecture and our open-source implementation.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

};

export default articles;
