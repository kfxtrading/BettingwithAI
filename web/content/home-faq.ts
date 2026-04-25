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
      'Betting with AI is an independent football analytics platform that turns complex match data into clear, structured insights. Instead of relying on gut feeling or hype, the platform provides data-driven probability estimates and identifies selected opportunities where the numbers may suggest potential value. All insights are designed to support smarter decision-making — not to guarantee outcomes. Football remains unpredictable, and every user is responsible for their own choices.',
  },
  {
    question: 'How does AI-based football prediction work on this site?',
    answer:
      'Our AI-based football prediction system analyzes a wide range of football and market signals to estimate how likely different match outcomes are. The goal is not to predict the future with certainty, but to create a more structured view of a match than simple intuition or public opinion can provide. When the system detects a meaningful difference between its own assessment and the market view, it may highlight the match as a potential value opportunity. All predictions should be seen as analytical guidance, not guaranteed results.',
  },
  {
    question: 'What is a value bet?',
    answer:
      'A value bet is a situation where the available odds may be higher than what the data suggests they should be. In simple terms: the platform looks for matches where the market may be underestimating a certain outcome. These opportunities are not guarantees — even strong value bets can lose. The idea is not to win every single bet, but to identify decisions that may be more favorable over time when handled responsibly.',
  },
  {
    question: 'How accurate are the predictions?',
    answer:
      'Prediction quality is measured over time, not by the result of a single match. Betting with AI focuses on producing well-balanced probability estimates and tracking performance transparently across completed matches. This helps users understand how the platform performs in real conditions rather than relying on isolated wins or losses. Football will always involve uncertainty, so predictions should be viewed as data-driven guidance — not as guaranteed outcomes.',
  },
  {
    question: 'Which data sources are used?',
    answer:
      'Betting with AI uses trusted football, match and market-related data to create structured pre-match insights. The platform combines historical results, current football context and available market signals to support its probability assessments. Data is handled carefully and selectively, with the goal of keeping the analysis consistent, responsible and focused on quality rather than noise. We do not disclose every internal data process publicly, but the purpose remains simple: provide clearer, data-driven football insights while respecting uncertainty.',
  },
  {
    question: 'How is the Kelly criterion used for stakes?',
    answer:
      'The Kelly criterion is used as a responsible staking framework to suggest stake sizes in relation to the user’s bankroll. Instead of recommending fixed amounts, the platform expresses stakes as percentages. This keeps the approach scalable and helps avoid oversized positions. Stake suggestions are designed to support disciplined decision-making, not aggressive risk-taking. Users should always adjust stakes to their own risk tolerance and never bet more than they can afford to lose.',
  },
  {
    question: 'Is the service free?',
    answer:
      'Yes — the core version of Betting with AI is currently free to use. Users can access daily football insights, match probabilities and selected value opportunities without registration. The platform is designed as an analytics tool, not as a bookmaker, betting service or affiliate-driven tipster site. In the future, additional premium features may be introduced for users who want deeper analysis, advanced filters or more detailed performance insights. The main goal remains the same: making football data easier to understand and use responsibly.',
  },
  {
    question: 'How does Betting with AI compare to Forebet and Sofascore?',
    answer:
      'Betting with AI is built with a different focus. Many football platforms are designed around live scores, broad statistics or high-volume match previews. Betting with AI focuses more narrowly on structured football analysis, probability-based insights and selected value opportunities. The goal is not to cover everything, but to make each prediction easier to understand, easier to compare and more transparent over time. It is designed for users who want a clean, data-driven view rather than generic football content.',
  },
  {
    question: 'How often is the snapshot updated?',
    answer:
      'Betting with AI is updated regularly to keep match insights as current and useful as possible. Predictions are typically refreshed once new daily football and market information becomes available. During active match periods, selected information may update more frequently where relevant. If an update is still in progress or data is not fully current, the platform aims to make this clear instead of showing outdated insights without context.',
  },
];
