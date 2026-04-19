export type Dictionary = Record<DictionaryKey, string>;

export type DictionaryKey =
  | 'site.title'
  | 'site.tagline'
  | 'site.description'
  | 'home.heading'
  | 'home.subheading'
  | 'home.loading'
  | 'home.section.valueBets.title'
  | 'home.section.valueBets.caption'
  | 'home.section.valueBets.empty.title'
  | 'home.section.valueBets.empty.hint'
  | 'home.section.predictions.title'
  | 'home.section.predictions.caption'
  | 'home.section.predictions.empty.title'
  | 'home.section.predictions.empty.hint'
  | 'leagues.label'
  | 'leagues.heading'
  | 'leagues.description'
  | 'leagues.teams'
  | 'leagues.leader'
  | 'leagues.noData'
  | 'leagues.viewDetails'
  | 'league.back'
  | 'league.subtitle'
  | 'league.section.table'
  | 'league.empty.title'
  | 'league.empty.hint'
  | 'performance.label'
  | 'performance.heading'
  | 'performance.description'
  | 'performance.section.coreMetrics'
  | 'performance.section.bankroll'
  | 'performance.section.bankroll.caption'
  | 'performance.section.byLeague'
  | 'performance.byLeague.empty'
  | 'performance.byLeague.col.league'
  | 'performance.byLeague.col.name'
  | 'performance.byLeague.col.bets'
  | 'performance.byLeague.col.hitRate'
  | 'performance.byLeague.col.roi'
  | 'kpi.bets'
  | 'kpi.bets.hint'
  | 'kpi.hitRate'
  | 'kpi.hitRate.noBets'
  | 'kpi.hitRate.hint'
  | 'kpi.roi'
  | 'kpi.maxDrawdown'
  | 'transparency.title'
  | 'transparency.updating'
  | 'transparency.disclaimer'
  | 'transparency.viewFullDetails'
  | 'recentBets.title'
  | 'recentBets.captionFallback'
  | 'recentBets.captionTemplate'
  | 'recentBets.day.bet'
  | 'recentBets.day.bets'
  | 'recentBets.day.day'
  | 'recentBets.day.days'
  | 'recentBets.day.pending'
  | 'recentBets.status.won'
  | 'recentBets.status.lost'
  | 'recentBets.status.pending'
  | 'recentBets.empty.title'
  | 'recentBets.empty.hint'
  | 'recentBets.updating'
  | 'predictionCard.outcome.home'
  | 'predictionCard.outcome.draw'
  | 'predictionCard.outcome.away'
  | 'predictionCard.pick'
  | 'predictionCard.vs'
  | 'valueBet.confidence.high'
  | 'valueBet.confidence.medium'
  | 'valueBet.confidence.low'
  | 'valueBet.odds'
  | 'valueBet.edge'
  | 'valueBet.stake'
  | 'bankroll.empty'
  | 'ratings.col.team'
  | 'ratings.col.home'
  | 'ratings.col.away'
  | 'ratings.col.overall'
  | 'ratings.col.form'
  | 'nav.today'
  | 'nav.performance'
  | 'nav.leagues'
  | 'nav.language'
  | 'footer.text'
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
  'home.loading': 'Loading predictions…',
  'home.section.valueBets.title': 'Value Bets',
  'home.section.valueBets.caption':
    'Discrepancies identified between model and market.',
  'home.section.valueBets.empty.title': 'No value bets right now',
  'home.section.valueBets.empty.hint':
    'When the model finds a significant edge over the market, opportunities will appear here.',
  'home.section.predictions.title': "Today's Predictions",
  'home.section.predictions.caption': 'Probabilities for Home · Draw · Away.',
  'home.section.predictions.empty.title': 'No predictions available',
  'home.section.predictions.empty.hint':
    'Generate a snapshot with `fb snapshot` or drop a fixtures file into "data/".',
  'leagues.label': 'Leagues',
  'leagues.heading': 'Pi-Ratings and form across every top league.',
  'leagues.description':
    'Browse Pi-Ratings, recent form and head-to-head data for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship.',
  'leagues.teams': '{n} teams',
  'leagues.leader': 'Leader:',
  'leagues.noData': 'No data yet — run `fb download`.',
  'leagues.viewDetails': 'View details →',
  'league.back': '← All leagues',
  'league.subtitle':
    'Pi-Ratings after Constantinou & Fenton (2013) — split by home and away strength.',
  'league.section.table': 'Table',
  'league.empty.title': 'No data',
  'league.empty.hint': 'Load league data with `fb download --league all`.',
  'performance.label': 'Model transparency',
  'performance.heading': 'Performance across the entire betting history.',
  'performance.description':
    'Full transparency over hit rate, ROI, max drawdown and per-league breakdowns — updated after every matchday.',
  'performance.section.coreMetrics': 'Core Metrics',
  'performance.section.bankroll': 'Bankroll Curve',
  'performance.section.bankroll.caption': 'Starting bankroll 1,000.',
  'performance.section.byLeague': 'Breakdown by League',
  'performance.byLeague.empty': 'No settled bets per league yet.',
  'performance.byLeague.col.league': 'League',
  'performance.byLeague.col.name': 'Name',
  'performance.byLeague.col.bets': 'Bets',
  'performance.byLeague.col.hitRate': 'Hit Rate',
  'performance.byLeague.col.roi': 'ROI',
  'kpi.bets': 'Bets',
  'kpi.bets.hint': '{n} predictions total',
  'kpi.hitRate': 'Hit rate',
  'kpi.hitRate.noBets': 'No settled bets yet',
  'kpi.hitRate.hint': 'Wins / settled bets',
  'kpi.roi': 'ROI',
  'kpi.maxDrawdown': 'Max drawdown',
  'transparency.title': 'Transparency Tracker',
  'transparency.updating': 'Performance data is being updated.',
  'transparency.disclaimer':
    'Hypothetical simulation of a statistical model based on historical match data. Not a solicitation to gamble. No guarantee of future results. Gambling involves financial risk.',
  'transparency.viewFullDetails': 'View full details',
  'recentBets.title': 'Recent Bets',
  'recentBets.captionFallback': 'Evaluation of past value bets',
  'recentBets.captionTemplate':
    'Last {n} {dayLabel} · {bets} bets · Hit rate {rate}',
  'recentBets.day.bet': 'Bet',
  'recentBets.day.bets': 'Bets',
  'recentBets.day.day': 'day',
  'recentBets.day.days': 'days',
  'recentBets.day.pending': '{n} pending',
  'recentBets.status.won': 'Won',
  'recentBets.status.lost': 'Lost',
  'recentBets.status.pending': 'Pending',
  'recentBets.empty.title': 'No settled bets yet',
  'recentBets.empty.hint':
    'As soon as the first matches finish, results will appear here with green/red evaluation.',
  'recentBets.updating': 'History is being updated.',
  'predictionCard.outcome.home': 'Home win',
  'predictionCard.outcome.draw': 'Draw',
  'predictionCard.outcome.away': 'Away win',
  'predictionCard.pick': 'Pick:',
  'predictionCard.vs': 'vs',
  'valueBet.confidence.high': 'High',
  'valueBet.confidence.medium': 'Medium',
  'valueBet.confidence.low': 'Low',
  'valueBet.odds': 'Odds',
  'valueBet.edge': 'Edge',
  'valueBet.stake': 'Stake',
  'bankroll.empty': 'No bankroll data yet — log some bets to start tracking.',
  'ratings.col.team': 'Team',
  'ratings.col.home': 'Home',
  'ratings.col.away': 'Away',
  'ratings.col.overall': 'Overall',
  'ratings.col.form': 'Form',
  'nav.today': 'Today',
  'nav.performance': 'Performance',
  'nav.leagues': 'Leagues',
  'nav.language': 'Language',
  'footer.text':
    'Betting with AI · CatBoost + Poisson + MLP ensemble · Model v0.3',
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
