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
  | 'home.section.valueBets.info.aria'
  | 'home.section.valueBets.info.body'
  | 'home.section.predictions.title'
  | 'home.section.predictions.caption'
  | 'home.section.predictions.empty.title'
  | 'home.section.predictions.empty.hint'
  | 'home.stale.title'
  | 'home.stale.hint'
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
  | 'recentBets.kind.value'
  | 'recentBets.kind.prediction'
  | 'predictionCard.outcome.home'
  | 'predictionCard.outcome.draw'
  | 'predictionCard.outcome.away'
  | 'predictionCard.pick'
  | 'predictionCard.vs'
  | 'predictionCard.badge.live'
  | 'predictionCard.badge.correct'
  | 'predictionCard.badge.incorrect'
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
  | 'nav.about'
  | 'nav.methodology'
  | 'footer.text'
  | 'footer.col.product'
  | 'footer.col.about'
  | 'footer.col.legal'
  | 'footer.col.responsible'
  | 'footer.link.today'
  | 'footer.link.leagues'
  | 'footer.link.performance'
  | 'footer.link.about'
  | 'footer.link.methodology'
  | 'footer.link.changelog'
  | 'footer.link.sourceCode'
  | 'footer.link.terms'
  | 'footer.link.privacy'
  | 'footer.link.cookies'
  | 'footer.link.impressum'
  | 'footer.link.responsibleGambling'
  | 'footer.link.helpline'
  | 'footer.disclaimer'
  | 'footer.ageBadge.label'
  | 'page.about.title'
  | 'page.about.description'
  | 'page.methodology.title'
  | 'page.methodology.description'
  | 'page.responsibleGambling.title'
  | 'page.responsibleGambling.description'
  | 'page.terms.title'
  | 'page.terms.description'
  | 'page.privacy.title'
  | 'page.privacy.description'
  | 'page.cookies.title'
  | 'page.cookies.description'
  | 'page.impressum.title'
  | 'page.impressum.description'
  | 'page.trackRecord.title'
  | 'page.trackRecord.description'
  | 'page.learn.title'
  | 'page.learn.description'
  | 'trackRecord.calibration.title'
  | 'trackRecord.calibration.caption'
  | 'trackRecord.csv.title'
  | 'trackRecord.csv.caption'
  | 'trackRecord.csv.button'
  | 'trackRecord.stats.records'
  | 'trackRecord.stats.settled'
  | 'learn.heading'
  | 'learn.intro'
  | 'learn.readMore'
  | 'leagueHub.next5.title'
  | 'leagueHub.next5.empty'
  | 'leagueHub.last5.title'
  | 'leagueHub.last5.empty'
  | 'leagueHub.pickCorrect'
  | 'leagueHub.pickIncorrect'
  | 'leagueHub.viewMatch'
  | 'match.lineups.title'
  | 'match.lineups.attribution'
  | 'match.lineups.consentPrompt'
  | 'match.lineups.consentNote'
  | 'match.lineups.consentButton'
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
  'home.section.valueBets.info.aria': 'About the stake calculation',
  'home.section.valueBets.info.body':
    'The stake is derived from the Kelly criterion: f* = (p · o − 1) / (o − 1), where p is our calibrated win probability and o the decimal odds. We apply a fractional Kelly (¼) and cap each bet at 5% of the bankroll to reduce variance.',
  'home.section.predictions.title': "Today's Predictions",
  'home.section.predictions.caption': 'Probabilities for Home · Draw · Away.',
  'home.section.predictions.empty.title': 'No predictions available',
  'home.section.predictions.empty.hint':
    'Generate a snapshot with `fb snapshot` or drop a fixtures file into "data/".',
  'home.stale.title': "Today's predictions are being generated",
  'home.stale.hint':
    'Fresh odds and model predictions are refreshed every morning. Please reload in a few minutes.',
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
  'recentBets.kind.value': 'Value',
  'recentBets.kind.prediction': 'Pick',
  'predictionCard.outcome.home': 'Home win',
  'predictionCard.outcome.draw': 'Draw',
  'predictionCard.outcome.away': 'Away win',
  'predictionCard.pick': 'Pick:',
  'predictionCard.vs': 'vs',
  'predictionCard.badge.live': 'Live',
  'predictionCard.badge.correct': 'Pick correct',
  'predictionCard.badge.incorrect': 'Pick incorrect',
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
  'nav.about': 'About',
  'nav.methodology': 'Methodology',
  'footer.text':
    'Betting with AI · CatBoost + Poisson + MLP ensemble · Model v0.3',
  'footer.col.product': 'Product',
  'footer.col.about': 'About',
  'footer.col.legal': 'Legal',
  'footer.col.responsible': 'Responsible Gambling',
  'footer.link.today': "Today's predictions",
  'footer.link.leagues': 'Leagues',
  'footer.link.performance': 'Performance tracker',
  'footer.link.about': 'About',
  'footer.link.methodology': 'Methodology',
  'footer.link.changelog': 'Model changelog',
  'footer.link.sourceCode': 'Source code ↗',
  'footer.link.terms': 'Terms of Service',
  'footer.link.privacy': 'Privacy Policy',
  'footer.link.cookies': 'Cookies',
  'footer.link.impressum': 'Impressum',
  'footer.link.responsibleGambling': 'Responsible Gambling',
  'footer.link.helpline': 'GambleAware (UK helpline)',
  'footer.disclaimer':
    'Informational content only. Not betting advice. We do not accept stakes and do not earn commission from bookmakers. Past model performance is no guarantee of future results.',
  'footer.ageBadge.label': '18+ · Information only',
  'page.about.title': 'About Betting with AI',
  'page.about.description':
    'Independent, non-affiliate AI football analytics built by a solo data scientist. Why we exist, who we are, and how we differ from affiliate-driven prediction sites.',
  'page.methodology.title': 'Methodology · How our model works',
  'page.methodology.description':
    'Pi-Ratings, CatBoost, Dixon-Coles Poisson, MLP ensemble, isotonic calibration and walk-forward backtesting — every component explained transparently.',
  'page.responsibleGambling.title': 'Responsible Gambling',
  'page.responsibleGambling.description':
    'Help, self-exclusion tools and national helplines for problem gambling across the UK, Germany, France, Italy and Spain.',
  'page.terms.title': 'Terms of Service',
  'page.terms.description':
    'Legal terms governing your use of Betting with AI. Educational content only — we are not a bookmaker and never accept wagers.',
  'page.privacy.title': 'Privacy Policy',
  'page.privacy.description':
    'How Betting with AI handles personal data, cookies and analytics under GDPR.',
  'page.cookies.title': 'Cookie Policy',
  'page.cookies.description':
    'Which cookies we set, why, and how to manage your preferences.',
  'page.impressum.title': 'Impressum',
  'page.impressum.description':
    'Anbieterkennzeichnung gemäß § 5 DDG (vormals § 5 TMG) und § 18 MStV.',
  'page.trackRecord.title': 'Track Record · Verified accuracy',
  'page.trackRecord.description':
    'Public, downloadable history of every Betting with AI prediction vs the actual result, with calibration plot and CSV download. No cherry-picking.',
  'page.learn.title': 'Learn · Football betting concepts',
  'page.learn.description':
    'Plain-language guides to value bets, expected goals, the Kelly criterion, model calibration and more — by an independent AI football analyst.',
  'trackRecord.calibration.title': 'Calibration plot',
  'trackRecord.calibration.caption':
    'Predicted probability vs observed frequency across all settled outcomes. The diagonal is perfect calibration.',
  'trackRecord.csv.title': 'Download the full dataset',
  'trackRecord.csv.caption':
    'Every prediction, with model probabilities, the actual result and a correctness flag. CSV, UTF-8.',
  'trackRecord.csv.button': 'Download track-record.csv',
  'trackRecord.stats.records': 'Predictions logged',
  'trackRecord.stats.settled': 'Settled (with result)',
  'learn.heading': 'Football betting concepts, in plain language.',
  'learn.intro':
    'Short, evidence-based guides to value bets, model calibration, bankroll management and the metrics this site is judged on.',
  'learn.readMore': 'Read →',
  'leagueHub.next5.title': 'Next 5 fixtures',
  'leagueHub.next5.empty': 'No upcoming fixtures in the current snapshot.',
  'leagueHub.last5.title': 'Last 5 results',
  'leagueHub.last5.empty': 'No recent results available yet.',
  'leagueHub.pickCorrect': 'Pick correct',
  'leagueHub.pickIncorrect': 'Pick incorrect',
  'leagueHub.viewMatch': 'Open prediction →',
  'match.lineups.title': 'Lineups & player ratings',
  'match.lineups.attribution': 'Live lineup data by Sofascore',
  'match.lineups.consentPrompt':
    'Live lineups with Sofascore player ratings are available for this match.',
  'match.lineups.consentNote':
    'Loading the widget transmits data to sofascore.com and sets third-party cookies.',
  'match.lineups.consentButton': 'Load Sofascore lineups',
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
