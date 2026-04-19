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
  | 'performance.description'
  | 'cookie.title'
  | 'cookie.body'
  | 'cookie.necessary.title'
  | 'cookie.necessary.desc'
  | 'cookie.analytics.title'
  | 'cookie.analytics.desc'
  | 'cookie.marketing.title'
  | 'cookie.marketing.desc'
  | 'cookie.btn.settings'
  | 'cookie.btn.hideDetails'
  | 'cookie.btn.reject'
  | 'cookie.btn.save'
  | 'cookie.btn.acceptAll'
  | 'cookie.aria.dialog';

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
  'cookie.title': 'We use cookies',
  'cookie.body':
    'This site uses cookies and similar technologies to keep the service running and to measure reach and performance. Your choice is stored together with a hash of your IP address so we can recognise it on your next visit. You can withdraw it at any time.',
  'cookie.necessary.title': 'Necessary',
  'cookie.necessary.desc': 'Required for the site to work. Always on.',
  'cookie.analytics.title': 'Statistics',
  'cookie.analytics.desc': 'Anonymous usage measurement to improve the site.',
  'cookie.marketing.title': 'Marketing',
  'cookie.marketing.desc': 'Personalised content and third-party tracking.',
  'cookie.btn.settings': 'Settings',
  'cookie.btn.hideDetails': 'Hide details',
  'cookie.btn.reject': 'Reject',
  'cookie.btn.save': 'Save selection',
  'cookie.btn.acceptAll': 'Accept all',
  'cookie.aria.dialog': 'Cookie consent',
};
