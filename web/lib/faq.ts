import Fuse from 'fuse.js';
import type { DictionaryKey } from './i18n';

export interface FaqEntry {
  id: string;
  questionKey: DictionaryKey;
  answerKey: DictionaryKey;
  tags: string[];
}

export const FAQ_ENTRIES: FaqEntry[] = [
  {
    id: 'value-bet',
    questionKey: 'support.faq.valueBet.q',
    answerKey: 'support.faq.valueBet.a',
    tags: ['value', 'bet', 'edge', 'wette', 'wert', 'odds', 'quote', 'kelly'],
  },
  {
    id: 'accuracy',
    questionKey: 'support.faq.accuracy.q',
    answerKey: 'support.faq.accuracy.a',
    tags: [
      'accuracy',
      'genauigkeit',
      'model',
      'modell',
      'prediction',
      'vorhersage',
      'rps',
      'brier',
    ],
  },
  {
    id: 'data-source',
    questionKey: 'support.faq.dataSource.q',
    answerKey: 'support.faq.dataSource.a',
    tags: [
      'data',
      'daten',
      'source',
      'quelle',
      'football-data',
      'sofascore',
      'odds',
    ],
  },
  {
    id: 'snapshot-update',
    questionKey: 'support.faq.snapshotUpdate.q',
    answerKey: 'support.faq.snapshotUpdate.a',
    tags: [
      'snapshot',
      'update',
      'refresh',
      'aktualisierung',
      'time',
      'zeit',
      'wann',
    ],
  },
  {
    id: 'kelly',
    questionKey: 'support.faq.kelly.q',
    answerKey: 'support.faq.kelly.a',
    tags: ['kelly', 'stake', 'einsatz', 'bankroll', 'risk', 'risiko', 'staking'],
  },
  {
    id: 'pi-rating',
    questionKey: 'support.faq.piRating.q',
    answerKey: 'support.faq.piRating.a',
    tags: ['pi', 'rating', 'elo', 'strength', 'stärke', 'staerke', 'team'],
  },
  {
    id: 'responsible',
    questionKey: 'support.faq.responsible.q',
    answerKey: 'support.faq.responsible.a',
    tags: [
      'responsible',
      'verantwortung',
      'gambling',
      'spielsucht',
      'advice',
      'beratung',
      'financial',
    ],
  },
  {
    id: 'language',
    questionKey: 'support.faq.language.q',
    answerKey: 'support.faq.language.a',
    tags: ['language', 'sprache', 'locale', 'translation', 'übersetzung'],
  },
  {
    id: 'cookies',
    questionKey: 'support.faq.cookies.q',
    answerKey: 'support.faq.cookies.a',
    tags: ['cookie', 'cookies', 'consent', 'einwilligung', 'privacy', 'datenschutz'],
  },
  {
    id: 'contact',
    questionKey: 'support.faq.contact.q',
    answerKey: 'support.faq.contact.a',
    tags: ['contact', 'kontakt', 'email', 'support', 'hilfe', 'help'],
  },
  {
    id: 'basics-1x2',
    questionKey: 'support.faq.basics.oneX2.q',
    answerKey: 'support.faq.basics.oneX2.a',
    tags: ['1x2', 'heim', 'auswärts', 'home', 'away', 'draw', 'unentschieden', 'markt', 'market'],
  },
  {
    id: 'basics-odds',
    questionKey: 'support.faq.basics.odds.q',
    answerKey: 'support.faq.basics.odds.a',
    tags: ['quoten', 'odds', 'decimal', 'dezimal', 'quote', 'cote', 'cuota'],
  },
  {
    id: 'basics-winnings',
    questionKey: 'support.faq.basics.winnings.q',
    answerKey: 'support.faq.basics.winnings.a',
    tags: ['gewinn', 'auszahlung', 'berechnen', 'payout', 'calculate', 'profit'],
  },
  {
    id: 'basics-single',
    questionKey: 'support.faq.basics.single.q',
    answerKey: 'support.faq.basics.single.a',
    tags: ['einzelwette', 'single', 'einzel'],
  },
  {
    id: 'basics-accumulator',
    questionKey: 'support.faq.basics.accumulator.q',
    answerKey: 'support.faq.basics.accumulator.a',
    tags: ['kombi', 'accumulator', 'combo', 'parlay', 'kombiwette'],
  },
  {
    id: 'basics-system',
    questionKey: 'support.faq.basics.system.q',
    answerKey: 'support.faq.basics.system.a',
    tags: ['system', 'systemwette'],
  },
  {
    id: 'basics-valuebet',
    questionKey: 'support.faq.basics.valueBetBasic.q',
    answerKey: 'support.faq.basics.valueBetBasic.a',
    tags: ['value', 'edge', '+ev', 'wert'],
  },
  {
    id: 'basics-probability',
    questionKey: 'support.faq.basics.probability.q',
    answerKey: 'support.faq.basics.probability.a',
    tags: ['wahrscheinlichkeit', 'probability', 'implied', 'implizit'],
  },
  {
    id: 'basics-bookie',
    questionKey: 'support.faq.basics.bookie.q',
    answerKey: 'support.faq.basics.bookie.a',
    tags: ['buchmacher', 'bookmaker', 'bookie', 'anbieter'],
  },
  {
    id: 'basics-bookiemoney',
    questionKey: 'support.faq.basics.bookieMoney.q',
    answerKey: 'support.faq.basics.bookieMoney.a',
    tags: ['marge', 'overround', 'bookmaker', 'profit', 'vig'],
  },
  {
    id: 'basics-overround',
    questionKey: 'support.faq.basics.overround.q',
    answerKey: 'support.faq.basics.overround.a',
    tags: ['overround', 'marge', 'margin', 'vig', 'juice'],
  },
  {
    id: 'basics-live',
    questionKey: 'support.faq.basics.live.q',
    answerKey: 'support.faq.basics.live.a',
    tags: ['live', 'in-play', 'livewette'],
  },
  {
    id: 'basics-cashout',
    questionKey: 'support.faq.basics.cashout.q',
    answerKey: 'support.faq.basics.cashout.a',
    tags: ['cashout', 'cash-out', 'auszahlen'],
  },
  {
    id: 'basics-handicap',
    questionKey: 'support.faq.basics.handicap.q',
    answerKey: 'support.faq.basics.handicap.a',
    tags: ['handicap', 'asiatisch', 'asian', 'spread'],
  },
  {
    id: 'basics-asianhandicap',
    questionKey: 'support.faq.basics.asianHandicap.q',
    answerKey: 'support.faq.basics.asianHandicap.a',
    tags: ['asian', 'handicap', 'viertel', 'halb'],
  },
  {
    id: 'basics-ou25',
    questionKey: 'support.faq.basics.ou25.q',
    answerKey: 'support.faq.basics.ou25.a',
    tags: ['over', 'under', '2.5', 'totale', 'tore', 'goals'],
  },
  {
    id: 'basics-btts',
    questionKey: 'support.faq.basics.btts.q',
    answerKey: 'support.faq.basics.btts.a',
    tags: ['btts', 'both', 'teams', 'score', 'tor'],
  },
  {
    id: 'basics-dnb',
    questionKey: 'support.faq.basics.dnb.q',
    answerKey: 'support.faq.basics.dnb.a',
    tags: ['draw', 'no', 'bet', 'dnb', 'remis'],
  },
  {
    id: 'basics-doublechance',
    questionKey: 'support.faq.basics.doubleChance.q',
    answerKey: 'support.faq.basics.doubleChance.a',
    tags: ['double', 'chance', 'doppelt'],
  },
  {
    id: 'basics-specials',
    questionKey: 'support.faq.basics.specials.q',
    answerKey: 'support.faq.basics.specials.a',
    tags: ['spezial', 'special', 'torschütze', 'scorer'],
  },
  {
    id: 'analysis-howto',
    questionKey: 'support.faq.analysis.howTo.q',
    answerKey: 'support.faq.analysis.howTo.a',
    tags: ['analyse', 'spiel', 'analyze', 'match'],
  },
  {
    id: 'analysis-stats',
    questionKey: 'support.faq.analysis.stats.q',
    answerKey: 'support.faq.analysis.stats.a',
    tags: ['stats', 'statistik', 'xg', 'shots', 'schüsse'],
  },
  {
    id: 'analysis-form',
    questionKey: 'support.faq.analysis.form.q',
    answerKey: 'support.faq.analysis.form.a',
    tags: ['form', 'aktuell', 'momentum', 'streak'],
  },
  {
    id: 'analysis-homeaway',
    questionKey: 'support.faq.analysis.homeAway.q',
    answerKey: 'support.faq.analysis.homeAway.a',
    tags: ['heim', 'auswärts', 'home', 'away', 'advantage'],
  },
  {
    id: 'analysis-injuries',
    questionKey: 'support.faq.analysis.injuries.q',
    answerKey: 'support.faq.analysis.injuries.a',
    tags: ['verletzung', 'injury', 'ausfall', 'sperre'],
  },
  {
    id: 'analysis-lineups',
    questionKey: 'support.faq.analysis.lineups.q',
    answerKey: 'support.faq.analysis.lineups.a',
    tags: ['aufstellung', 'lineup', 'starting'],
  },
  {
    id: 'analysis-xg',
    questionKey: 'support.faq.analysis.xg.q',
    answerKey: 'support.faq.analysis.xg.a',
    tags: ['xg', 'expected', 'goals'],
  },
  {
    id: 'analysis-h2h',
    questionKey: 'support.faq.analysis.h2h.q',
    answerKey: 'support.faq.analysis.h2h.a',
    tags: ['h2h', 'direkt', 'head-to-head'],
  },
  {
    id: 'analysis-motivation',
    questionKey: 'support.faq.analysis.motivation.q',
    answerKey: 'support.faq.analysis.motivation.a',
    tags: ['motivation', 'abstieg', 'titel', 'pokal'],
  },
  {
    id: 'analysis-weather',
    questionKey: 'support.faq.analysis.weather.q',
    answerKey: 'support.faq.analysis.weather.a',
    tags: ['wetter', 'regen', 'wind', 'weather'],
  },
  {
    id: 'analysis-deffoff',
    questionKey: 'support.faq.analysis.defOff.q',
    answerKey: 'support.faq.analysis.defOff.a',
    tags: ['defensiv', 'offensiv', 'defense', 'offense'],
  },
  {
    id: 'analysis-goalstats',
    questionKey: 'support.faq.analysis.goalStats.q',
    answerKey: 'support.faq.analysis.goalStats.a',
    tags: ['tore', 'goals', 'torstatistik'],
  },
  {
    id: 'analysis-bestleague',
    questionKey: 'support.faq.analysis.bestLeague.q',
    answerKey: 'support.faq.analysis.bestLeague.a',
    tags: ['liga', 'league', 'vorhersagbar'],
  },
  {
    id: 'analysis-coach',
    questionKey: 'support.faq.analysis.coach.q',
    answerKey: 'support.faq.analysis.coach.a',
    tags: ['trainer', 'coach', 'wechsel'],
  },
  {
    id: 'analysis-tempo',
    questionKey: 'support.faq.analysis.tempo.q',
    answerKey: 'support.faq.analysis.tempo.a',
    tags: ['tempo', 'taktik', 'tactics', 'pace'],
  },
  {
    id: 'analysis-ougames',
    questionKey: 'support.faq.analysis.ouGames.q',
    answerKey: 'support.faq.analysis.ouGames.a',
    tags: ['over', 'under', 'ou', 'tore'],
  },
  {
    id: 'analysis-bttsgames',
    questionKey: 'support.faq.analysis.bttsGames.q',
    answerKey: 'support.faq.analysis.bttsGames.a',
    tags: ['btts', 'both', 'score'],
  },
  {
    id: 'analysis-draws',
    questionKey: 'support.faq.analysis.draws.q',
    answerKey: 'support.faq.analysis.draws.a',
    tags: ['unentschieden', 'draw', 'remis'],
  },
  {
    id: 'analysis-underdogs',
    questionKey: 'support.faq.analysis.underdogs.q',
    answerKey: 'support.faq.analysis.underdogs.a',
    tags: ['underdog', 'außenseiter', 'outsider'],
  },
  {
    id: 'analysis-trapgames',
    questionKey: 'support.faq.analysis.trapGames.q',
    answerKey: 'support.faq.analysis.trapGames.a',
    tags: ['trap', 'falle', 'rotation', 'cup'],
  },
  {
    id: 'strategy-best',
    questionKey: 'support.faq.strategy.best.q',
    answerKey: 'support.faq.strategy.best.a',
    tags: ['strategie', 'best', 'beste', 'strategy'],
  },
  {
    id: 'strategy-value',
    questionKey: 'support.faq.strategy.valueBet.q',
    answerKey: 'support.faq.strategy.valueBet.a',
    tags: ['value', 'edge', 'betting'],
  },
  {
    id: 'strategy-arbitrage',
    questionKey: 'support.faq.strategy.arbitrage.q',
    answerKey: 'support.faq.strategy.arbitrage.a',
    tags: ['arbitrage', 'surebet'],
  },
  {
    id: 'strategy-martingale',
    questionKey: 'support.faq.strategy.martingale.q',
    answerKey: 'support.faq.strategy.martingale.a',
    tags: ['martingale', 'progression', 'doubling'],
  },
  {
    id: 'strategy-flat',
    questionKey: 'support.faq.strategy.flat.q',
    answerKey: 'support.faq.strategy.flat.a',
    tags: ['flat', 'staking'],
  },
  {
    id: 'strategy-bankroll',
    questionKey: 'support.faq.strategy.bankroll.q',
    answerKey: 'support.faq.strategy.bankroll.a',
    tags: ['bankroll', 'kapital', 'management'],
  },
  {
    id: 'strategy-stake',
    questionKey: 'support.faq.strategy.stake.q',
    answerKey: 'support.faq.strategy.stake.a',
    tags: ['einsatz', 'stake', 'size'],
  },
  {
    id: 'strategy-losingstreak',
    questionKey: 'support.faq.strategy.losingStreak.q',
    answerKey: 'support.faq.strategy.losingStreak.a',
    tags: ['verlust', 'streak', 'drawdown'],
  },
  {
    id: 'strategy-combos',
    questionKey: 'support.faq.strategy.combos.q',
    answerKey: 'support.faq.strategy.combos.a',
    tags: ['kombi', 'parlay', 'combo'],
  },
  {
    id: 'strategy-profitable',
    questionKey: 'support.faq.strategy.profitable.q',
    answerKey: 'support.faq.strategy.profitable.a',
    tags: ['profitabel', 'langfristig', 'long-term'],
  },
  {
    id: 'strategy-test',
    questionKey: 'support.faq.strategy.test.q',
    answerKey: 'support.faq.strategy.test.a',
    tags: ['test', 'backtest', 'validieren'],
  },
  {
    id: 'strategy-roi',
    questionKey: 'support.faq.strategy.roi.q',
    answerKey: 'support.faq.strategy.roi.a',
    tags: ['roi', 'return', 'investment'],
  },
  {
    id: 'strategy-strikerate',
    questionKey: 'support.faq.strategy.strikeRate.q',
    answerKey: 'support.faq.strategy.strikeRate.a',
    tags: ['strike', 'rate', 'trefferquote'],
  },
  {
    id: 'strategy-discipline',
    questionKey: 'support.faq.strategy.discipline.q',
    answerKey: 'support.faq.strategy.discipline.a',
    tags: ['disziplin', 'discipline'],
  },
  {
    id: 'strategy-goododds',
    questionKey: 'support.faq.strategy.goodOdds.q',
    answerKey: 'support.faq.strategy.goodOdds.a',
    tags: ['gute', 'schlechte', 'odds', 'quote'],
  },
  {
    id: 'strategy-nobet',
    questionKey: 'support.faq.strategy.noBet.q',
    answerKey: 'support.faq.strategy.noBet.a',
    tags: ['nicht', 'wetten', 'skip'],
  },
  {
    id: 'strategy-timing',
    questionKey: 'support.faq.strategy.timing.q',
    answerKey: 'support.faq.strategy.timing.a',
    tags: ['timing', 'wann', 'when'],
  },
  {
    id: 'strategy-prematchlive',
    questionKey: 'support.faq.strategy.prematchLive.q',
    answerKey: 'support.faq.strategy.prematchLive.a',
    tags: ['pre-match', 'live', 'in-play'],
  },
  {
    id: 'strategy-oddsmovement',
    questionKey: 'support.faq.strategy.oddsMovement.q',
    answerKey: 'support.faq.strategy.oddsMovement.a',
    tags: ['odds', 'movement', 'drift'],
  },
  {
    id: 'strategy-ownsystem',
    questionKey: 'support.faq.strategy.ownSystem.q',
    answerKey: 'support.faq.strategy.ownSystem.a',
    tags: ['eigenes', 'system', 'custom'],
  },
  {
    id: 'mistakes-losemoney',
    questionKey: 'support.faq.mistakes.loseMoney.q',
    answerKey: 'support.faq.mistakes.loseMoney.a',
    tags: ['verlieren', 'lose', 'money'],
  },
  {
    id: 'mistakes-chasing',
    questionKey: 'support.faq.mistakes.chasing.q',
    answerKey: 'support.faq.mistakes.chasing.a',
    tags: ['chasing', 'losses', 'verlust'],
  },
  {
    id: 'mistakes-emotions',
    questionKey: 'support.faq.mistakes.emotions.q',
    answerKey: 'support.faq.mistakes.emotions.a',
    tags: ['emotion', 'tilt'],
  },
  {
    id: 'mistakes-accumulators',
    questionKey: 'support.faq.mistakes.accumulators.q',
    answerKey: 'support.faq.mistakes.accumulators.a',
    tags: ['kombi', 'accumulator', 'riskant'],
  },
  {
    id: 'mistakes-overbetting',
    questionKey: 'support.faq.mistakes.overbetting.q',
    answerKey: 'support.faq.mistakes.overbetting.a',
    tags: ['overbetting', 'over', 'stake'],
  },
  {
    id: 'mistakes-tipsters',
    questionKey: 'support.faq.mistakes.tipsters.q',
    answerKey: 'support.faq.mistakes.tipsters.a',
    tags: ['tipster', 'experte', 'blind'],
  },
  {
    id: 'mistakes-nobankroll',
    questionKey: 'support.faq.mistakes.noBankroll.q',
    answerKey: 'support.faq.mistakes.noBankroll.a',
    tags: ['bankroll', 'no', 'fail'],
  },
  {
    id: 'mistakes-surebets',
    questionKey: 'support.faq.mistakes.sureBets.q',
    answerKey: 'support.faq.mistakes.sureBets.a',
    tags: ['sichere', 'tipps', 'sure'],
  },
  {
    id: 'mistakes-favteam',
    questionKey: 'support.faq.mistakes.favTeam.q',
    answerKey: 'support.faq.mistakes.favTeam.a',
    tags: ['lieblings', 'fav', 'bias'],
  },
  {
    id: 'mistakes-beginner',
    questionKey: 'support.faq.mistakes.beginner.q',
    answerKey: 'support.faq.mistakes.beginner.a',
    tags: ['anfänger', 'beginner', 'fehler'],
  },
  {
    id: 'ai-how',
    questionKey: 'support.faq.ai.how.q',
    answerKey: 'support.faq.ai.how.a',
    tags: ['ki', 'ai', 'prognose', 'prediction'],
  },
  {
    id: 'ai-data',
    questionKey: 'support.faq.ai.data.q',
    answerKey: 'support.faq.ai.data.a',
    tags: ['daten', 'data', 'features'],
  },
  {
    id: 'ai-reliability',
    questionKey: 'support.faq.ai.reliability.q',
    answerKey: 'support.faq.ai.reliability.a',
    tags: ['zuverlässig', 'reliable', 'accuracy'],
  },
  {
    id: 'ai-model',
    questionKey: 'support.faq.ai.model.q',
    answerKey: 'support.faq.ai.model.a',
    tags: ['model', 'modell', 'prediction'],
  },
  {
    id: 'ai-ml',
    questionKey: 'support.faq.ai.ml.q',
    answerKey: 'support.faq.ai.ml.a',
    tags: ['ml', 'machine', 'learning'],
  },
  {
    id: 'ai-features',
    questionKey: 'support.faq.ai.features.q',
    answerKey: 'support.faq.ai.features.a',
    tags: ['features', 'variablen'],
  },
  {
    id: 'ai-history',
    questionKey: 'support.faq.ai.history.q',
    answerKey: 'support.faq.ai.history.a',
    tags: ['historisch', 'history', 'daten'],
  },
  {
    id: 'ai-oddsmodel',
    questionKey: 'support.faq.ai.oddsModel.q',
    answerKey: 'support.faq.ai.oddsModel.a',
    tags: ['odds', 'model', 'quote'],
  },
  {
    id: 'ai-valuebet',
    questionKey: 'support.faq.ai.valueBet.q',
    answerKey: 'support.faq.ai.valueBet.a',
    tags: ['value', 'ki', 'edge'],
  },
  {
    id: 'ai-overfitting',
    questionKey: 'support.faq.ai.overfitting.q',
    answerKey: 'support.faq.ai.overfitting.a',
    tags: ['overfitting', 'regulation'],
  },
  {
    id: 'ai-algorithms',
    questionKey: 'support.faq.ai.algorithms.q',
    answerKey: 'support.faq.ai.algorithms.a',
    tags: ['algorithm', 'randomforest', 'catboost'],
  },
  {
    id: 'ai-livedata',
    questionKey: 'support.faq.ai.liveData.q',
    answerKey: 'support.faq.ai.liveData.a',
    tags: ['live', 'daten', 'echtzeit'],
  },
  {
    id: 'ai-realtime',
    questionKey: 'support.faq.ai.realtime.q',
    answerKey: 'support.faq.ai.realtime.a',
    tags: ['echtzeit', 'realtime', 'update'],
  },
  {
    id: 'ai-measure',
    questionKey: 'support.faq.ai.measure.q',
    answerKey: 'support.faq.ai.measure.a',
    tags: ['genauigkeit', 'accuracy', 'metric'],
  },
  {
    id: 'ai-improve',
    questionKey: 'support.faq.ai.improve.q',
    answerKey: 'support.faq.ai.improve.a',
    tags: ['verbessern', 'improve', 'model'],
  },
  {
    id: 'ai-combine',
    questionKey: 'support.faq.ai.combine.q',
    answerKey: 'support.faq.ai.combine.a',
    tags: ['kombinieren', 'combine', 'ensemble'],
  },
  {
    id: 'ai-ensemble',
    questionKey: 'support.faq.ai.ensemble.q',
    answerKey: 'support.faq.ai.ensemble.a',
    tags: ['ensemble', 'stacking', 'betting'],
  },
  {
    id: 'ai-apis',
    questionKey: 'support.faq.ai.apis.q',
    answerKey: 'support.faq.ai.apis.a',
    tags: ['api', 'feed', 'daten'],
  },
  {
    id: 'ai-dashboard',
    questionKey: 'support.faq.ai.dashboard.q',
    answerKey: 'support.faq.ai.dashboard.a',
    tags: ['dashboard', 'ui', 'visualisierung'],
  },
  {
    id: 'ai-automate',
    questionKey: 'support.faq.ai.automate.q',
    answerKey: 'support.faq.ai.automate.a',
    tags: ['automatisieren', 'automate', 'cron'],
  },
  {
    id: 'market-create',
    questionKey: 'support.faq.market.create.q',
    answerKey: 'support.faq.market.create.a',
    tags: ['quoten', 'entstehen', 'odds'],
  },
  {
    id: 'market-change',
    questionKey: 'support.faq.market.change.q',
    answerKey: 'support.faq.market.change.a',
    tags: ['ändern', 'change', 'move'],
  },
  {
    id: 'market-clv',
    questionKey: 'support.faq.market.clv.q',
    answerKey: 'support.faq.market.clv.a',
    tags: ['clv', 'closing', 'line', 'value'],
  },
  {
    id: 'market-valueOdds',
    questionKey: 'support.faq.market.valueOdds.q',
    answerKey: 'support.faq.market.valueOdds.a',
    tags: ['value', 'quote', 'erkennen'],
  },
  {
    id: 'market-bestbooks',
    questionKey: 'support.faq.market.bestBooks.q',
    answerKey: 'support.faq.market.bestBooks.a',
    tags: ['buchmacher', 'beste', 'bookmaker'],
  },
  {
    id: 'market-diffbooks',
    questionKey: 'support.faq.market.diffBooks.q',
    answerKey: 'support.faq.market.diffBooks.a',
    tags: ['unterschied', 'bookmaker', 'diff'],
  },
  {
    id: 'market-compare',
    questionKey: 'support.faq.market.compare.q',
    answerKey: 'support.faq.market.compare.a',
    tags: ['odds', 'compare', 'vergleich'],
  },
  {
    id: 'market-sharppublic',
    questionKey: 'support.faq.market.sharpPublic.q',
    answerKey: 'support.faq.market.sharpPublic.a',
    tags: ['sharp', 'public', 'money'],
  },
  {
    id: 'market-movement',
    questionKey: 'support.faq.market.movement.q',
    answerKey: 'support.faq.market.movement.a',
    tags: ['bewegung', 'movement', 'drift'],
  },
  {
    id: 'market-liquidity',
    questionKey: 'support.faq.market.liquidity.q',
    answerKey: 'support.faq.market.liquidity.a',
    tags: ['liquidität', 'liquidity', 'volume'],
  },
  {
    id: 'profit-earn',
    questionKey: 'support.faq.profit.earn.q',
    answerKey: 'support.faq.profit.earn.a',
    tags: ['geld', 'verdienen', 'profit'],
  },
  {
    id: 'profit-longterm',
    questionKey: 'support.faq.profit.longterm.q',
    answerKey: 'support.faq.profit.longterm.a',
    tags: ['langfristig', 'chance', 'winrate'],
  },
  {
    id: 'profit-roi',
    questionKey: 'support.faq.profit.roi.q',
    answerKey: 'support.faq.profit.roi.a',
    tags: ['roi', 'realistisch'],
  },
  {
    id: 'profit-timeToProfit',
    questionKey: 'support.faq.profit.timeToProfit.q',
    answerKey: 'support.faq.profit.timeToProfit.a',
    tags: ['dauer', 'profitabel', 'zeit'],
  },
  {
    id: 'profit-capital',
    questionKey: 'support.faq.profit.capital.q',
    answerKey: 'support.faq.profit.capital.a',
    tags: ['kapital', 'bankroll', 'startgeld'],
  },
  {
    id: 'profit-skillVsLuck',
    questionKey: 'support.faq.profit.skillVsLuck.q',
    answerKey: 'support.faq.profit.skillVsLuck.a',
    tags: ['skill', 'glück', 'luck'],
  },
  {
    id: 'profit-prosVsAmateurs',
    questionKey: 'support.faq.profit.prosVsAmateurs.q',
    answerKey: 'support.faq.profit.prosVsAmateurs.a',
    tags: ['profi', 'amateur', 'unterschied'],
  },
  {
    id: 'profit-prosWork',
    questionKey: 'support.faq.profit.prosWork.q',
    answerKey: 'support.faq.profit.prosWork.a',
    tags: ['profi', 'arbeit', 'routine'],
  },
  {
    id: 'profit-patience',
    questionKey: 'support.faq.profit.patience.q',
    answerKey: 'support.faq.profit.patience.a',
    tags: ['geduld', 'patience'],
  },
  {
    id: 'profit-fail90',
    questionKey: 'support.faq.profit.fail90.q',
    answerKey: 'support.faq.profit.fail90.a',
    tags: ['scheitern', '90', 'verlieren'],
  },
  {
    id: 'platform-daily',
    questionKey: 'support.faq.platform.daily.q',
    answerKey: 'support.faq.platform.daily.a',
    tags: ['täglich', 'daily', 'prediction'],
  },
  {
    id: 'platform-autoload',
    questionKey: 'support.faq.platform.autoload.q',
    answerKey: 'support.faq.platform.autoload.a',
    tags: ['spiele', 'laden', 'api'],
  },
  {
    id: 'platform-updateFreq',
    questionKey: 'support.faq.platform.updateFreq.q',
    answerKey: 'support.faq.platform.updateFreq.a',
    tags: ['update', 'frequenz', 'häufig'],
  },
  {
    id: 'platform-confidence',
    questionKey: 'support.faq.platform.confidence.q',
    answerKey: 'support.faq.platform.confidence.a',
    tags: ['confidence', 'score'],
  },
  {
    id: 'platform-visualize',
    questionKey: 'support.faq.platform.visualize.q',
    answerKey: 'support.faq.platform.visualize.a',
    tags: ['visualisieren', 'visualize', 'chart'],
  },
  {
    id: 'platform-bestbets',
    questionKey: 'support.faq.platform.bestBets.q',
    answerKey: 'support.faq.platform.bestBets.a',
    tags: ['beste', 'wetten', 'filter'],
  },
  {
    id: 'platform-history',
    questionKey: 'support.faq.platform.history.q',
    answerKey: 'support.faq.platform.history.a',
    tags: ['historisch', 'performance', 'track'],
  },
  {
    id: 'platform-tracking',
    questionKey: 'support.faq.platform.tracking.q',
    answerKey: 'support.faq.platform.tracking.a',
    tags: ['user', 'tracking', 'analytics'],
  },
  {
    id: 'platform-ranking',
    questionKey: 'support.faq.platform.ranking.q',
    answerKey: 'support.faq.platform.ranking.a',
    tags: ['ranking', 'tipps', 'rank'],
  },
  {
    id: 'platform-lastBets',
    questionKey: 'support.faq.platform.lastBets.q',
    answerKey: 'support.faq.platform.lastBets.a',
    tags: ['letzte', 'bets', 'recent'],
  },
  {
    id: 'platform-wrongMatch',
    questionKey: 'support.faq.platform.wrongMatch.q',
    answerKey: 'support.faq.platform.wrongMatch.a',
    tags: ['falsch', 'spiele', 'bug'],
  },
  {
    id: 'platform-valueVsPrediction',
    questionKey: 'support.faq.platform.valueVsPrediction.q',
    answerKey: 'support.faq.platform.valueVsPrediction.a',
    tags: ['value', 'prediction', 'unterschied'],
  },
  {
    id: 'platform-alerts',
    questionKey: 'support.faq.platform.alerts.q',
    answerKey: 'support.faq.platform.alerts.a',
    tags: ['alert', 'notification', 'benachrichtigung'],
  },
  {
    id: 'platform-trust',
    questionKey: 'support.faq.platform.trust.q',
    answerKey: 'support.faq.platform.trust.a',
    tags: ['vertrauen', 'trust', 'transparenz'],
  },
];

import {
  buildVocab,
  normalizeQuery,
  normalizeText,
  type NormalizedQuery,
} from './faqNormalize';

export interface SearchableEntry {
  id: string;
  question: string;
  questionNorm: string;
  tags: string[];
  tagsNorm: string[];
}

export interface FaqMatch {
  entry: FaqEntry;
  score: number;
}

export interface FaqIndex {
  fuse: Fuse<SearchableEntry>;
  vocab: Set<string>;
  vocabList: string[];
  /** Map from normalized-tag token → list of entry IDs that carry it. */
  tagIndex: Map<string, string[]>;
}

export function buildFuse(t: (key: DictionaryKey) => string): FaqIndex {
  const searchable: SearchableEntry[] = FAQ_ENTRIES.map((e) => {
    const question = t(e.questionKey);
    return {
      id: e.id,
      question,
      questionNorm: normalizeText(question),
      tags: e.tags,
      tagsNorm: e.tags.map((tag) => normalizeText(tag)).filter(Boolean),
    };
  });

  // Vocabulary: tag tokens + question tokens from the current locale.
  const vocabSources: string[] = [];
  for (const s of searchable) {
    vocabSources.push(s.questionNorm, ...s.tagsNorm);
  }
  const { vocab, vocabList } = buildVocab(vocabSources);

  // Reverse index for fast keyword-hit scoring.
  const tagIndex = new Map<string, string[]>();
  for (const s of searchable) {
    const tokens = new Set<string>();
    for (const tn of s.tagsNorm) {
      for (const tok of tn.split(' ')) if (tok) tokens.add(tok);
    }
    for (const tok of s.questionNorm.split(' ')) {
      if (tok.length >= 4) tokens.add(tok);
    }
    for (const tok of tokens) {
      const bucket = tagIndex.get(tok);
      if (bucket) bucket.push(s.id);
      else tagIndex.set(tok, [s.id]);
    }
  }

  const fuse = new Fuse(searchable, {
    keys: [
      { name: 'question', weight: 0.35 },
      { name: 'questionNorm', weight: 0.35 },
      { name: 'tags', weight: 0.15 },
      { name: 'tagsNorm', weight: 0.15 },
    ],
    threshold: 0.45,
    includeScore: true,
    ignoreLocation: true,
    minMatchCharLength: 2,
  });

  return { fuse, vocab, vocabList, tagIndex };
}

/**
 * Search the FAQ index with robustness against case, punctuation,
 * diacritics, concatenated words and small typos.
 *
 * Strategy:
 *   1. Normalize the query (+ split concatenated words, + typo-correct tokens).
 *   2. Run Fuse.js on BOTH the raw-normalized and the canonical form.
 *   3. Add a direct token-intersection boost from `tagIndex` so short tag
 *      queries like "btts" or "kelly" win deterministically.
 *   4. Merge by entry id, keep the best (lowest) score per entry.
 */
export function searchFaq(query: string, index: FaqIndex): FaqMatch[] {
  const q = query.trim();
  if (!q) return [];

  const nq: NormalizedQuery = normalizeQuery(q, index.vocab, index.vocabList);
  const byId = new Map(FAQ_ENTRIES.map((e) => [e.id, e]));
  const bestScore = new Map<string, number>();

  const record = (id: string, score: number) => {
    const prev = bestScore.get(id);
    if (prev === undefined || score < prev) bestScore.set(id, score);
  };

  // 1) Fuse on raw user input (catches idiomatic / sentence-style questions).
  for (const r of index.fuse.search(q).slice(0, 8)) {
    record(r.item.id, r.score ?? 1);
  }

  // 2) Fuse on the canonical form (handles case, punct, concat splits, typos).
  if (nq.canonical && nq.canonical !== q.toLowerCase()) {
    for (const r of index.fuse.search(nq.canonical).slice(0, 8)) {
      // Slightly penalise so an exact raw hit still wins ties.
      record(r.item.id, (r.score ?? 1) + 0.01);
    }
  }

  // 3) Deterministic tag-token intersection — boost entries whose tags match
  //    any canonical token exactly. Great for single-keyword inputs.
  const hitCounts = new Map<string, number>();
  for (const tok of nq.tokens) {
    if (tok.length < 2) continue;
    const ids = index.tagIndex.get(tok);
    if (!ids) continue;
    for (const id of ids) hitCounts.set(id, (hitCounts.get(id) ?? 0) + 1);
  }
  if (hitCounts.size > 0) {
    const totalTokens = Math.max(1, nq.tokens.length);
    for (const [id, hits] of hitCounts) {
      // Coverage ratio → pseudo-score in [0, 0.5]; more hits → lower (better) score.
      const coverage = Math.min(1, hits / totalTokens);
      const score = 0.5 - 0.4 * coverage;
      record(id, score);
    }
  }

  const matches: FaqMatch[] = [];
  for (const [id, score] of bestScore) {
    const entry = byId.get(id);
    if (entry) matches.push({ entry, score });
  }
  matches.sort((a, b) => a.score - b.score);
  return matches.slice(0, 4);
}
