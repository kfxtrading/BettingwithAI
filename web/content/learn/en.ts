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
    title: 'Kelly Criterion for Sports Betting: Formula, Examples, Limits',
    description:
      'The Kelly criterion sizes each bet to maximise long-term geometric growth of your bankroll. Here is the formula, a worked football example and why most pros use fractional Kelly.',
    tldr:
      'Kelly stake = (bp − q) / b, where b is decimal_odds − 1, p is your win probability and q is 1 − p. Most professionals use a quarter or half of that to control variance.',
    sections: [
      {
        heading: 'The formula and a worked example',
        paragraphs: [
          'You believe Manchester City beat Arsenal with probability 0.55. The odds are 2.10 (so b = 1.10). Kelly = (1.10 × 0.55 − 0.45) / 1.10 = 0.155 / 1.10 ≈ 14.1% of bankroll.',
          'Half-Kelly would stake 7%, quarter-Kelly 3.5%. Full Kelly is mathematically optimal only if your probabilities are exact — they never are.',
        ],
      },
      {
        heading: 'Why fractional Kelly',
        paragraphs: [
          'Full Kelly is brutally volatile: even an unbiased estimator with realistic noise produces 30–50% drawdowns. Fractional Kelly trades a small amount of long-term return for a much smaller drawdown — usually a winning trade.',
          'Always cap any single stake at 1–3% of bankroll regardless of what Kelly says, and refuse negative-EV bets entirely.',
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
          'Technically yes, but parlay variance is so high that Kelly stakes are tiny. Most quants avoid parlays except for hedging.',
      },
      {
        question: 'How do I size if I bet on multiple matches at once?',
        answer:
          'Use simultaneous Kelly: solve a small optimisation that sizes each bet jointly subject to a total-stake constraint. Or apply per-bet Kelly and cap total exposure at 25–30% of bankroll.',
      },
    ],
    lastUpdated: LAST_UPDATED,
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
};

export default articles;
