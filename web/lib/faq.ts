import Fuse from 'fuse.js';
import type { DictionaryKey } from './i18n';

export interface FaqEntry {
  id: string;
  questionKey: DictionaryKey;
  answerKey: DictionaryKey;
  tags: string[];
  /** id of another FaqEntry that represents the natural follow-up. */
  followUpId?: string;
  /** additional localized question strings the user might type (same intent). */
  altQuestionKeys?: DictionaryKey[];
}

export const FAQ_ENTRIES: FaqEntry[] = [
  {
    id: 'value-bet',
    questionKey: 'support.faq.valueBet.q',
    answerKey: 'support.faq.valueBet.a',
    tags: ['value', 'bet', 'edge', 'wette', 'wert', 'odds', 'quote', 'kelly'],
    followUpId: 'value-bet-fu',
    altQuestionKeys: ['support.faq.valueBet.alt1', 'support.faq.valueBet.alt2', 'support.faq.valueBet.alt3', 'support.faq.valueBet.alt4', 'support.faq.valueBet.alt5'],},
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
    followUpId: 'accuracy-fu',
    altQuestionKeys: ['support.faq.accuracy.alt1', 'support.faq.accuracy.alt2', 'support.faq.accuracy.alt3', 'support.faq.accuracy.alt4', 'support.faq.accuracy.alt5'],},
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
    followUpId: 'data-source-fu',
    altQuestionKeys: ['support.faq.dataSource.alt1', 'support.faq.dataSource.alt2', 'support.faq.dataSource.alt3', 'support.faq.dataSource.alt4', 'support.faq.dataSource.alt5'],},
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
    followUpId: 'snapshot-update-fu',
    altQuestionKeys: ['support.faq.snapshotUpdate.alt1', 'support.faq.snapshotUpdate.alt2', 'support.faq.snapshotUpdate.alt3', 'support.faq.snapshotUpdate.alt4', 'support.faq.snapshotUpdate.alt5'],},
  {
    id: 'kelly',
    questionKey: 'support.faq.kelly.q',
    answerKey: 'support.faq.kelly.a',
    tags: ['kelly', 'stake', 'einsatz', 'bankroll', 'risk', 'risiko', 'staking'],
    followUpId: 'kelly-fu',
    altQuestionKeys: ['support.faq.kelly.alt1', 'support.faq.kelly.alt2', 'support.faq.kelly.alt3', 'support.faq.kelly.alt4', 'support.faq.kelly.alt5'],},
  {
    id: 'pi-rating',
    questionKey: 'support.faq.piRating.q',
    answerKey: 'support.faq.piRating.a',
    tags: ['pi', 'rating', 'elo', 'strength', 'stärke', 'staerke', 'team'],
    followUpId: 'pi-rating-fu',
    altQuestionKeys: ['support.faq.piRating.alt1', 'support.faq.piRating.alt2', 'support.faq.piRating.alt3', 'support.faq.piRating.alt4', 'support.faq.piRating.alt5'],},
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
    followUpId: 'responsible-fu',
    altQuestionKeys: ['support.faq.responsible.alt1', 'support.faq.responsible.alt2', 'support.faq.responsible.alt3', 'support.faq.responsible.alt4', 'support.faq.responsible.alt5'],},
  {
    id: 'language',
    questionKey: 'support.faq.language.q',
    answerKey: 'support.faq.language.a',
    tags: ['language', 'sprache', 'locale', 'translation', 'übersetzung'],
    followUpId: 'language-fu',
    altQuestionKeys: ['support.faq.language.alt1', 'support.faq.language.alt2', 'support.faq.language.alt3', 'support.faq.language.alt4', 'support.faq.language.alt5'],},
  {
    id: 'cookies',
    questionKey: 'support.faq.cookies.q',
    answerKey: 'support.faq.cookies.a',
    tags: ['cookie', 'cookies', 'consent', 'einwilligung', 'privacy', 'datenschutz'],
    followUpId: 'cookies-fu',
    altQuestionKeys: ['support.faq.cookies.alt1', 'support.faq.cookies.alt2', 'support.faq.cookies.alt3', 'support.faq.cookies.alt4', 'support.faq.cookies.alt5'],},
  {
    id: 'contact',
    questionKey: 'support.faq.contact.q',
    answerKey: 'support.faq.contact.a',
    tags: ['contact', 'kontakt', 'email', 'support', 'hilfe', 'help'],
    followUpId: 'contact-fu',
    altQuestionKeys: ['support.faq.contact.alt1', 'support.faq.contact.alt2', 'support.faq.contact.alt3', 'support.faq.contact.alt4', 'support.faq.contact.alt5'],},
  {
    id: 'basics-1x2',
    questionKey: 'support.faq.basics.oneX2.q',
    answerKey: 'support.faq.basics.oneX2.a',
    tags: ['1x2', 'heim', 'auswärts', 'home', 'away', 'draw', 'unentschieden', 'markt', 'market'],
    followUpId: 'basics-1x2-fu',
    altQuestionKeys: ['support.faq.basics.oneX2.alt1', 'support.faq.basics.oneX2.alt2', 'support.faq.basics.oneX2.alt3', 'support.faq.basics.oneX2.alt4', 'support.faq.basics.oneX2.alt5'],},
  {
    id: 'basics-odds',
    questionKey: 'support.faq.basics.odds.q',
    answerKey: 'support.faq.basics.odds.a',
    tags: ['quoten', 'odds', 'decimal', 'dezimal', 'quote', 'cote', 'cuota'],
    followUpId: 'basics-odds-fu',
    altQuestionKeys: ['support.faq.basics.odds.alt1', 'support.faq.basics.odds.alt2', 'support.faq.basics.odds.alt3', 'support.faq.basics.odds.alt4', 'support.faq.basics.odds.alt5'],},
  {
    id: 'basics-winnings',
    questionKey: 'support.faq.basics.winnings.q',
    answerKey: 'support.faq.basics.winnings.a',
    tags: ['gewinn', 'auszahlung', 'berechnen', 'payout', 'calculate', 'profit'],
    followUpId: 'basics-winnings-fu',
    altQuestionKeys: ['support.faq.basics.winnings.alt1', 'support.faq.basics.winnings.alt2', 'support.faq.basics.winnings.alt3', 'support.faq.basics.winnings.alt4', 'support.faq.basics.winnings.alt5'],},
  {
    id: 'basics-single',
    questionKey: 'support.faq.basics.single.q',
    answerKey: 'support.faq.basics.single.a',
    tags: ['einzelwette', 'single', 'einzel'],
    followUpId: 'basics-single-fu',
    altQuestionKeys: ['support.faq.basics.single.alt1', 'support.faq.basics.single.alt2', 'support.faq.basics.single.alt3', 'support.faq.basics.single.alt4', 'support.faq.basics.single.alt5'],},
  {
    id: 'basics-accumulator',
    questionKey: 'support.faq.basics.accumulator.q',
    answerKey: 'support.faq.basics.accumulator.a',
    tags: ['kombi', 'accumulator', 'combo', 'parlay', 'kombiwette'],
    followUpId: 'basics-accumulator-fu',
    altQuestionKeys: ['support.faq.basics.accumulator.alt1', 'support.faq.basics.accumulator.alt2', 'support.faq.basics.accumulator.alt3', 'support.faq.basics.accumulator.alt4', 'support.faq.basics.accumulator.alt5'],},
  {
    id: 'basics-system',
    questionKey: 'support.faq.basics.system.q',
    answerKey: 'support.faq.basics.system.a',
    tags: ['system', 'systemwette'],
    followUpId: 'basics-system-fu',
    altQuestionKeys: ['support.faq.basics.system.alt1', 'support.faq.basics.system.alt2', 'support.faq.basics.system.alt3', 'support.faq.basics.system.alt4', 'support.faq.basics.system.alt5'],},
  {
    id: 'basics-valuebet',
    questionKey: 'support.faq.basics.valueBetBasic.q',
    answerKey: 'support.faq.basics.valueBetBasic.a',
    tags: ['value', 'edge', '+ev', 'wert'],
    followUpId: 'basics-valuebet-fu',
    altQuestionKeys: ['support.faq.basics.valueBetBasic.alt1', 'support.faq.basics.valueBetBasic.alt2', 'support.faq.basics.valueBetBasic.alt3', 'support.faq.basics.valueBetBasic.alt4', 'support.faq.basics.valueBetBasic.alt5'],},
  {
    id: 'basics-probability',
    questionKey: 'support.faq.basics.probability.q',
    answerKey: 'support.faq.basics.probability.a',
    tags: ['wahrscheinlichkeit', 'probability', 'implied', 'implizit'],
    followUpId: 'basics-probability-fu',
    altQuestionKeys: ['support.faq.basics.probability.alt1', 'support.faq.basics.probability.alt2', 'support.faq.basics.probability.alt3', 'support.faq.basics.probability.alt4', 'support.faq.basics.probability.alt5'],},
  {
    id: 'basics-bookie',
    questionKey: 'support.faq.basics.bookie.q',
    answerKey: 'support.faq.basics.bookie.a',
    tags: ['buchmacher', 'bookmaker', 'bookie', 'anbieter'],
    followUpId: 'basics-bookie-fu',
    altQuestionKeys: ['support.faq.basics.bookie.alt1', 'support.faq.basics.bookie.alt2', 'support.faq.basics.bookie.alt3', 'support.faq.basics.bookie.alt4', 'support.faq.basics.bookie.alt5'],},
  {
    id: 'basics-bookiemoney',
    questionKey: 'support.faq.basics.bookieMoney.q',
    answerKey: 'support.faq.basics.bookieMoney.a',
    tags: ['marge', 'overround', 'bookmaker', 'profit', 'vig'],
    followUpId: 'basics-bookiemoney-fu',
    altQuestionKeys: ['support.faq.basics.bookieMoney.alt1', 'support.faq.basics.bookieMoney.alt2', 'support.faq.basics.bookieMoney.alt3', 'support.faq.basics.bookieMoney.alt4', 'support.faq.basics.bookieMoney.alt5'],},
  {
    id: 'basics-overround',
    questionKey: 'support.faq.basics.overround.q',
    answerKey: 'support.faq.basics.overround.a',
    tags: ['overround', 'marge', 'margin', 'vig', 'juice'],
    followUpId: 'basics-overround-fu',
    altQuestionKeys: ['support.faq.basics.overround.alt1', 'support.faq.basics.overround.alt2', 'support.faq.basics.overround.alt3', 'support.faq.basics.overround.alt4', 'support.faq.basics.overround.alt5'],},
  {
    id: 'basics-live',
    questionKey: 'support.faq.basics.live.q',
    answerKey: 'support.faq.basics.live.a',
    tags: ['live', 'in-play', 'livewette'],
    followUpId: 'basics-live-fu',
    altQuestionKeys: ['support.faq.basics.live.alt1', 'support.faq.basics.live.alt2', 'support.faq.basics.live.alt3', 'support.faq.basics.live.alt4', 'support.faq.basics.live.alt5'],},
  {
    id: 'basics-cashout',
    questionKey: 'support.faq.basics.cashout.q',
    answerKey: 'support.faq.basics.cashout.a',
    tags: ['cashout', 'cash-out', 'auszahlen'],
    followUpId: 'basics-cashout-fu',
    altQuestionKeys: ['support.faq.basics.cashout.alt1', 'support.faq.basics.cashout.alt2', 'support.faq.basics.cashout.alt3', 'support.faq.basics.cashout.alt4', 'support.faq.basics.cashout.alt5'],},
  {
    id: 'basics-handicap',
    questionKey: 'support.faq.basics.handicap.q',
    answerKey: 'support.faq.basics.handicap.a',
    tags: ['handicap', 'asiatisch', 'asian', 'spread'],
    followUpId: 'basics-handicap-fu',
    altQuestionKeys: ['support.faq.basics.handicap.alt1', 'support.faq.basics.handicap.alt2', 'support.faq.basics.handicap.alt3', 'support.faq.basics.handicap.alt4', 'support.faq.basics.handicap.alt5'],},
  {
    id: 'basics-asianhandicap',
    questionKey: 'support.faq.basics.asianHandicap.q',
    answerKey: 'support.faq.basics.asianHandicap.a',
    tags: ['asian', 'handicap', 'viertel', 'halb'],
    followUpId: 'basics-asianhandicap-fu',
    altQuestionKeys: ['support.faq.basics.asianHandicap.alt1', 'support.faq.basics.asianHandicap.alt2', 'support.faq.basics.asianHandicap.alt3', 'support.faq.basics.asianHandicap.alt4', 'support.faq.basics.asianHandicap.alt5'],},
  {
    id: 'basics-ou25',
    questionKey: 'support.faq.basics.ou25.q',
    answerKey: 'support.faq.basics.ou25.a',
    tags: ['over', 'under', '2.5', 'totale', 'tore', 'goals'],
    followUpId: 'basics-ou25-fu',
    altQuestionKeys: ['support.faq.basics.ou25.alt1', 'support.faq.basics.ou25.alt2', 'support.faq.basics.ou25.alt3', 'support.faq.basics.ou25.alt4', 'support.faq.basics.ou25.alt5'],},
  {
    id: 'basics-btts',
    questionKey: 'support.faq.basics.btts.q',
    answerKey: 'support.faq.basics.btts.a',
    tags: ['btts', 'both', 'teams', 'score', 'tor'],
    followUpId: 'basics-btts-fu',
    altQuestionKeys: ['support.faq.basics.btts.alt1', 'support.faq.basics.btts.alt2', 'support.faq.basics.btts.alt3', 'support.faq.basics.btts.alt4', 'support.faq.basics.btts.alt5'],},
  {
    id: 'basics-dnb',
    questionKey: 'support.faq.basics.dnb.q',
    answerKey: 'support.faq.basics.dnb.a',
    tags: ['draw', 'no', 'bet', 'dnb', 'remis'],
    followUpId: 'basics-dnb-fu',
    altQuestionKeys: ['support.faq.basics.dnb.alt1', 'support.faq.basics.dnb.alt2', 'support.faq.basics.dnb.alt3', 'support.faq.basics.dnb.alt4', 'support.faq.basics.dnb.alt5'],},
  {
    id: 'basics-doublechance',
    questionKey: 'support.faq.basics.doubleChance.q',
    answerKey: 'support.faq.basics.doubleChance.a',
    tags: ['double', 'chance', 'doppelt'],
    followUpId: 'basics-doublechance-fu',
    altQuestionKeys: ['support.faq.basics.doubleChance.alt1', 'support.faq.basics.doubleChance.alt2', 'support.faq.basics.doubleChance.alt3', 'support.faq.basics.doubleChance.alt4', 'support.faq.basics.doubleChance.alt5'],},
  {
    id: 'basics-specials',
    questionKey: 'support.faq.basics.specials.q',
    answerKey: 'support.faq.basics.specials.a',
    tags: ['spezial', 'special', 'torschütze', 'scorer'],
    followUpId: 'basics-specials-fu',
    altQuestionKeys: ['support.faq.basics.specials.alt1', 'support.faq.basics.specials.alt2', 'support.faq.basics.specials.alt3', 'support.faq.basics.specials.alt4', 'support.faq.basics.specials.alt5'],},
  {
    id: 'analysis-howto',
    questionKey: 'support.faq.analysis.howTo.q',
    answerKey: 'support.faq.analysis.howTo.a',
    tags: ['analyse', 'spiel', 'analyze', 'match'],
    followUpId: 'analysis-howto-fu',},
  {
    id: 'analysis-stats',
    questionKey: 'support.faq.analysis.stats.q',
    answerKey: 'support.faq.analysis.stats.a',
    tags: ['stats', 'statistik', 'xg', 'shots', 'schüsse'],
    followUpId: 'analysis-stats-fu',},
  {
    id: 'analysis-form',
    questionKey: 'support.faq.analysis.form.q',
    answerKey: 'support.faq.analysis.form.a',
    tags: ['form', 'aktuell', 'momentum', 'streak'],
    followUpId: 'analysis-form-fu',},
  {
    id: 'analysis-homeaway',
    questionKey: 'support.faq.analysis.homeAway.q',
    answerKey: 'support.faq.analysis.homeAway.a',
    tags: ['heim', 'auswärts', 'home', 'away', 'advantage'],
    followUpId: 'analysis-homeaway-fu',},
  {
    id: 'analysis-injuries',
    questionKey: 'support.faq.analysis.injuries.q',
    answerKey: 'support.faq.analysis.injuries.a',
    tags: ['verletzung', 'injury', 'ausfall', 'sperre'],
    followUpId: 'analysis-injuries-fu',},
  {
    id: 'analysis-lineups',
    questionKey: 'support.faq.analysis.lineups.q',
    answerKey: 'support.faq.analysis.lineups.a',
    tags: ['aufstellung', 'lineup', 'starting'],
    followUpId: 'analysis-lineups-fu',},
  {
    id: 'analysis-xg',
    questionKey: 'support.faq.analysis.xg.q',
    answerKey: 'support.faq.analysis.xg.a',
    tags: ['xg', 'expected', 'goals'],
    followUpId: 'analysis-xg-fu',},
  {
    id: 'analysis-h2h',
    questionKey: 'support.faq.analysis.h2h.q',
    answerKey: 'support.faq.analysis.h2h.a',
    tags: ['h2h', 'direkt', 'head-to-head'],
    followUpId: 'analysis-h2h-fu',},
  {
    id: 'analysis-motivation',
    questionKey: 'support.faq.analysis.motivation.q',
    answerKey: 'support.faq.analysis.motivation.a',
    tags: ['motivation', 'abstieg', 'titel', 'pokal'],
    followUpId: 'analysis-motivation-fu',},
  {
    id: 'analysis-weather',
    questionKey: 'support.faq.analysis.weather.q',
    answerKey: 'support.faq.analysis.weather.a',
    tags: ['wetter', 'regen', 'wind', 'weather'],
    followUpId: 'analysis-weather-fu',},
  {
    id: 'analysis-deffoff',
    questionKey: 'support.faq.analysis.defOff.q',
    answerKey: 'support.faq.analysis.defOff.a',
    tags: ['defensiv', 'offensiv', 'defense', 'offense'],
    followUpId: 'analysis-deffoff-fu',},
  {
    id: 'analysis-goalstats',
    questionKey: 'support.faq.analysis.goalStats.q',
    answerKey: 'support.faq.analysis.goalStats.a',
    tags: ['tore', 'goals', 'torstatistik'],
    followUpId: 'analysis-goalstats-fu',},
  {
    id: 'analysis-bestleague',
    questionKey: 'support.faq.analysis.bestLeague.q',
    answerKey: 'support.faq.analysis.bestLeague.a',
    tags: ['liga', 'league', 'vorhersagbar'],
    followUpId: 'analysis-bestleague-fu',},
  {
    id: 'analysis-coach',
    questionKey: 'support.faq.analysis.coach.q',
    answerKey: 'support.faq.analysis.coach.a',
    tags: ['trainer', 'coach', 'wechsel'],
    followUpId: 'analysis-coach-fu',},
  {
    id: 'analysis-tempo',
    questionKey: 'support.faq.analysis.tempo.q',
    answerKey: 'support.faq.analysis.tempo.a',
    tags: ['tempo', 'taktik', 'tactics', 'pace'],
    followUpId: 'analysis-tempo-fu',},
  {
    id: 'analysis-ougames',
    questionKey: 'support.faq.analysis.ouGames.q',
    answerKey: 'support.faq.analysis.ouGames.a',
    tags: ['over', 'under', 'ou', 'tore'],
    followUpId: 'analysis-ougames-fu',},
  {
    id: 'analysis-bttsgames',
    questionKey: 'support.faq.analysis.bttsGames.q',
    answerKey: 'support.faq.analysis.bttsGames.a',
    tags: ['btts', 'both', 'score'],
    followUpId: 'analysis-bttsgames-fu',},
  {
    id: 'analysis-draws',
    questionKey: 'support.faq.analysis.draws.q',
    answerKey: 'support.faq.analysis.draws.a',
    tags: ['unentschieden', 'draw', 'remis'],
    followUpId: 'analysis-draws-fu',},
  {
    id: 'analysis-underdogs',
    questionKey: 'support.faq.analysis.underdogs.q',
    answerKey: 'support.faq.analysis.underdogs.a',
    tags: ['underdog', 'außenseiter', 'outsider'],
    followUpId: 'analysis-underdogs-fu',},
  {
    id: 'analysis-trapgames',
    questionKey: 'support.faq.analysis.trapGames.q',
    answerKey: 'support.faq.analysis.trapGames.a',
    tags: ['trap', 'falle', 'rotation', 'cup'],
    followUpId: 'analysis-trapgames-fu',},
  {
    id: 'strategy-best',
    questionKey: 'support.faq.strategy.best.q',
    answerKey: 'support.faq.strategy.best.a',
    tags: ['strategie', 'best', 'beste', 'strategy'],
    followUpId: 'strategy-best-fu',},
  {
    id: 'strategy-value',
    questionKey: 'support.faq.strategy.valueBet.q',
    answerKey: 'support.faq.strategy.valueBet.a',
    tags: ['value', 'edge', 'betting'],
    followUpId: 'strategy-value-fu',},
  {
    id: 'strategy-arbitrage',
    questionKey: 'support.faq.strategy.arbitrage.q',
    answerKey: 'support.faq.strategy.arbitrage.a',
    tags: ['arbitrage', 'surebet'],
    followUpId: 'strategy-arbitrage-fu',},
  {
    id: 'strategy-martingale',
    questionKey: 'support.faq.strategy.martingale.q',
    answerKey: 'support.faq.strategy.martingale.a',
    tags: ['martingale', 'progression', 'doubling'],
    followUpId: 'strategy-martingale-fu',},
  {
    id: 'strategy-flat',
    questionKey: 'support.faq.strategy.flat.q',
    answerKey: 'support.faq.strategy.flat.a',
    tags: ['flat', 'staking'],
    followUpId: 'strategy-flat-fu',},
  {
    id: 'strategy-bankroll',
    questionKey: 'support.faq.strategy.bankroll.q',
    answerKey: 'support.faq.strategy.bankroll.a',
    tags: ['bankroll', 'kapital', 'management'],
    followUpId: 'strategy-bankroll-fu',},
  {
    id: 'strategy-stake',
    questionKey: 'support.faq.strategy.stake.q',
    answerKey: 'support.faq.strategy.stake.a',
    tags: ['einsatz', 'stake', 'size'],
    followUpId: 'strategy-stake-fu',},
  {
    id: 'strategy-losingstreak',
    questionKey: 'support.faq.strategy.losingStreak.q',
    answerKey: 'support.faq.strategy.losingStreak.a',
    tags: ['verlust', 'streak', 'drawdown'],
    followUpId: 'strategy-losingstreak-fu',},
  {
    id: 'strategy-combos',
    questionKey: 'support.faq.strategy.combos.q',
    answerKey: 'support.faq.strategy.combos.a',
    tags: ['kombi', 'parlay', 'combo'],
    followUpId: 'strategy-combos-fu',},
  {
    id: 'strategy-profitable',
    questionKey: 'support.faq.strategy.profitable.q',
    answerKey: 'support.faq.strategy.profitable.a',
    tags: ['profitabel', 'langfristig', 'long-term'],
    followUpId: 'strategy-profitable-fu',},
  {
    id: 'strategy-test',
    questionKey: 'support.faq.strategy.test.q',
    answerKey: 'support.faq.strategy.test.a',
    tags: ['test', 'backtest', 'validieren'],
    followUpId: 'strategy-test-fu',},
  {
    id: 'strategy-roi',
    questionKey: 'support.faq.strategy.roi.q',
    answerKey: 'support.faq.strategy.roi.a',
    tags: ['roi', 'return', 'investment'],
    followUpId: 'strategy-roi-fu',},
  {
    id: 'strategy-strikerate',
    questionKey: 'support.faq.strategy.strikeRate.q',
    answerKey: 'support.faq.strategy.strikeRate.a',
    tags: ['strike', 'rate', 'trefferquote'],
    followUpId: 'strategy-strikerate-fu',},
  {
    id: 'strategy-discipline',
    questionKey: 'support.faq.strategy.discipline.q',
    answerKey: 'support.faq.strategy.discipline.a',
    tags: ['disziplin', 'discipline'],
    followUpId: 'strategy-discipline-fu',},
  {
    id: 'strategy-goododds',
    questionKey: 'support.faq.strategy.goodOdds.q',
    answerKey: 'support.faq.strategy.goodOdds.a',
    tags: ['gute', 'schlechte', 'odds', 'quote'],
    followUpId: 'strategy-goododds-fu',},
  {
    id: 'strategy-nobet',
    questionKey: 'support.faq.strategy.noBet.q',
    answerKey: 'support.faq.strategy.noBet.a',
    tags: ['nicht', 'wetten', 'skip'],
    followUpId: 'strategy-nobet-fu',},
  {
    id: 'strategy-timing',
    questionKey: 'support.faq.strategy.timing.q',
    answerKey: 'support.faq.strategy.timing.a',
    tags: ['timing', 'wann', 'when'],
    followUpId: 'strategy-timing-fu',},
  {
    id: 'strategy-prematchlive',
    questionKey: 'support.faq.strategy.prematchLive.q',
    answerKey: 'support.faq.strategy.prematchLive.a',
    tags: ['pre-match', 'live', 'in-play'],
    followUpId: 'strategy-prematchlive-fu',},
  {
    id: 'strategy-oddsmovement',
    questionKey: 'support.faq.strategy.oddsMovement.q',
    answerKey: 'support.faq.strategy.oddsMovement.a',
    tags: ['odds', 'movement', 'drift'],
    followUpId: 'strategy-oddsmovement-fu',},
  {
    id: 'strategy-ownsystem',
    questionKey: 'support.faq.strategy.ownSystem.q',
    answerKey: 'support.faq.strategy.ownSystem.a',
    tags: ['eigenes', 'system', 'custom'],
    followUpId: 'strategy-ownsystem-fu',},
  {
    id: 'mistakes-losemoney',
    questionKey: 'support.faq.mistakes.loseMoney.q',
    answerKey: 'support.faq.mistakes.loseMoney.a',
    tags: ['verlieren', 'lose', 'money'],
    followUpId: 'mistakes-losemoney-fu',},
  {
    id: 'mistakes-chasing',
    questionKey: 'support.faq.mistakes.chasing.q',
    answerKey: 'support.faq.mistakes.chasing.a',
    tags: ['chasing', 'losses', 'verlust'],
    followUpId: 'mistakes-chasing-fu',},
  {
    id: 'mistakes-emotions',
    questionKey: 'support.faq.mistakes.emotions.q',
    answerKey: 'support.faq.mistakes.emotions.a',
    tags: ['emotion', 'tilt'],
    followUpId: 'mistakes-emotions-fu',},
  {
    id: 'mistakes-accumulators',
    questionKey: 'support.faq.mistakes.accumulators.q',
    answerKey: 'support.faq.mistakes.accumulators.a',
    tags: ['kombi', 'accumulator', 'riskant'],
    followUpId: 'mistakes-accumulators-fu',},
  {
    id: 'mistakes-overbetting',
    questionKey: 'support.faq.mistakes.overbetting.q',
    answerKey: 'support.faq.mistakes.overbetting.a',
    tags: ['overbetting', 'over', 'stake'],
    followUpId: 'mistakes-overbetting-fu',},
  {
    id: 'mistakes-tipsters',
    questionKey: 'support.faq.mistakes.tipsters.q',
    answerKey: 'support.faq.mistakes.tipsters.a',
    tags: ['tipster', 'experte', 'blind'],
    followUpId: 'mistakes-tipsters-fu',},
  {
    id: 'mistakes-nobankroll',
    questionKey: 'support.faq.mistakes.noBankroll.q',
    answerKey: 'support.faq.mistakes.noBankroll.a',
    tags: ['bankroll', 'no', 'fail'],
    followUpId: 'mistakes-nobankroll-fu',},
  {
    id: 'mistakes-surebets',
    questionKey: 'support.faq.mistakes.sureBets.q',
    answerKey: 'support.faq.mistakes.sureBets.a',
    tags: ['sichere', 'tipps', 'sure'],
    followUpId: 'mistakes-surebets-fu',},
  {
    id: 'mistakes-favteam',
    questionKey: 'support.faq.mistakes.favTeam.q',
    answerKey: 'support.faq.mistakes.favTeam.a',
    tags: ['lieblings', 'fav', 'bias'],
    followUpId: 'mistakes-favteam-fu',},
  {
    id: 'mistakes-beginner',
    questionKey: 'support.faq.mistakes.beginner.q',
    answerKey: 'support.faq.mistakes.beginner.a',
    tags: ['anfänger', 'beginner', 'fehler'],
    followUpId: 'mistakes-beginner-fu',},
  {
    id: 'ai-how',
    questionKey: 'support.faq.ai.how.q',
    answerKey: 'support.faq.ai.how.a',
    tags: ['ki', 'ai', 'prognose', 'prediction'],
    followUpId: 'ai-how-fu',},
  {
    id: 'ai-data',
    questionKey: 'support.faq.ai.data.q',
    answerKey: 'support.faq.ai.data.a',
    tags: ['daten', 'data', 'features'],
    followUpId: 'ai-data-fu',},
  {
    id: 'ai-reliability',
    questionKey: 'support.faq.ai.reliability.q',
    answerKey: 'support.faq.ai.reliability.a',
    tags: ['zuverlässig', 'reliable', 'accuracy'],
    followUpId: 'ai-reliability-fu',},
  {
    id: 'ai-model',
    questionKey: 'support.faq.ai.model.q',
    answerKey: 'support.faq.ai.model.a',
    tags: ['model', 'modell', 'prediction'],
    followUpId: 'ai-model-fu',},
  {
    id: 'ai-ml',
    questionKey: 'support.faq.ai.ml.q',
    answerKey: 'support.faq.ai.ml.a',
    tags: ['ml', 'machine', 'learning'],
    followUpId: 'ai-ml-fu',},
  {
    id: 'ai-features',
    questionKey: 'support.faq.ai.features.q',
    answerKey: 'support.faq.ai.features.a',
    tags: ['features', 'variablen'],
    followUpId: 'ai-features-fu',},
  {
    id: 'ai-history',
    questionKey: 'support.faq.ai.history.q',
    answerKey: 'support.faq.ai.history.a',
    tags: ['historisch', 'history', 'daten'],
    followUpId: 'ai-history-fu',},
  {
    id: 'ai-oddsmodel',
    questionKey: 'support.faq.ai.oddsModel.q',
    answerKey: 'support.faq.ai.oddsModel.a',
    tags: ['odds', 'model', 'quote'],
    followUpId: 'ai-oddsmodel-fu',},
  {
    id: 'ai-valuebet',
    questionKey: 'support.faq.ai.valueBet.q',
    answerKey: 'support.faq.ai.valueBet.a',
    tags: ['value', 'ki', 'edge'],
    followUpId: 'ai-valuebet-fu',},
  {
    id: 'ai-overfitting',
    questionKey: 'support.faq.ai.overfitting.q',
    answerKey: 'support.faq.ai.overfitting.a',
    tags: ['overfitting', 'regulation'],
    followUpId: 'ai-overfitting-fu',},
  {
    id: 'ai-algorithms',
    questionKey: 'support.faq.ai.algorithms.q',
    answerKey: 'support.faq.ai.algorithms.a',
    tags: ['algorithm', 'randomforest', 'catboost'],
    followUpId: 'ai-algorithms-fu',},
  {
    id: 'ai-livedata',
    questionKey: 'support.faq.ai.liveData.q',
    answerKey: 'support.faq.ai.liveData.a',
    tags: ['live', 'daten', 'echtzeit'],
    followUpId: 'ai-livedata-fu',},
  {
    id: 'ai-realtime',
    questionKey: 'support.faq.ai.realtime.q',
    answerKey: 'support.faq.ai.realtime.a',
    tags: ['echtzeit', 'realtime', 'update'],
    followUpId: 'ai-realtime-fu',},
  {
    id: 'ai-measure',
    questionKey: 'support.faq.ai.measure.q',
    answerKey: 'support.faq.ai.measure.a',
    tags: ['genauigkeit', 'accuracy', 'metric'],
    followUpId: 'ai-measure-fu',},
  {
    id: 'ai-improve',
    questionKey: 'support.faq.ai.improve.q',
    answerKey: 'support.faq.ai.improve.a',
    tags: ['verbessern', 'improve', 'model'],
    followUpId: 'ai-improve-fu',},
  {
    id: 'ai-combine',
    questionKey: 'support.faq.ai.combine.q',
    answerKey: 'support.faq.ai.combine.a',
    tags: ['kombinieren', 'combine', 'ensemble'],
    followUpId: 'ai-combine-fu',},
  {
    id: 'ai-ensemble',
    questionKey: 'support.faq.ai.ensemble.q',
    answerKey: 'support.faq.ai.ensemble.a',
    tags: ['ensemble', 'stacking', 'betting'],
    followUpId: 'ai-ensemble-fu',},
  {
    id: 'ai-apis',
    questionKey: 'support.faq.ai.apis.q',
    answerKey: 'support.faq.ai.apis.a',
    tags: ['api', 'feed', 'daten'],
    followUpId: 'ai-apis-fu',},
  {
    id: 'ai-dashboard',
    questionKey: 'support.faq.ai.dashboard.q',
    answerKey: 'support.faq.ai.dashboard.a',
    tags: ['dashboard', 'ui', 'visualisierung'],
    followUpId: 'ai-dashboard-fu',},
  {
    id: 'ai-automate',
    questionKey: 'support.faq.ai.automate.q',
    answerKey: 'support.faq.ai.automate.a',
    tags: ['automatisieren', 'automate', 'cron'],
    followUpId: 'ai-automate-fu',},
  {
    id: 'market-create',
    questionKey: 'support.faq.market.create.q',
    answerKey: 'support.faq.market.create.a',
    tags: ['quoten', 'entstehen', 'odds'],
    followUpId: 'market-create-fu',},
  {
    id: 'market-change',
    questionKey: 'support.faq.market.change.q',
    answerKey: 'support.faq.market.change.a',
    tags: ['ändern', 'change', 'move'],
    followUpId: 'market-change-fu',},
  {
    id: 'market-clv',
    questionKey: 'support.faq.market.clv.q',
    answerKey: 'support.faq.market.clv.a',
    tags: ['clv', 'closing', 'line', 'value'],
    followUpId: 'market-clv-fu',},
  {
    id: 'market-valueOdds',
    questionKey: 'support.faq.market.valueOdds.q',
    answerKey: 'support.faq.market.valueOdds.a',
    tags: ['value', 'quote', 'erkennen'],
    followUpId: 'market-valueOdds-fu',},
  {
    id: 'market-bestbooks',
    questionKey: 'support.faq.market.bestBooks.q',
    answerKey: 'support.faq.market.bestBooks.a',
    tags: ['buchmacher', 'beste', 'bookmaker'],
    followUpId: 'market-bestbooks-fu',},
  {
    id: 'market-diffbooks',
    questionKey: 'support.faq.market.diffBooks.q',
    answerKey: 'support.faq.market.diffBooks.a',
    tags: ['unterschied', 'bookmaker', 'diff'],
    followUpId: 'market-diffbooks-fu',},
  {
    id: 'market-compare',
    questionKey: 'support.faq.market.compare.q',
    answerKey: 'support.faq.market.compare.a',
    tags: ['odds', 'compare', 'vergleich'],
    followUpId: 'market-compare-fu',},
  {
    id: 'market-sharppublic',
    questionKey: 'support.faq.market.sharpPublic.q',
    answerKey: 'support.faq.market.sharpPublic.a',
    tags: ['sharp', 'public', 'money'],
    followUpId: 'market-sharppublic-fu',},
  {
    id: 'market-movement',
    questionKey: 'support.faq.market.movement.q',
    answerKey: 'support.faq.market.movement.a',
    tags: ['bewegung', 'movement', 'drift'],
    followUpId: 'market-movement-fu',},
  {
    id: 'market-liquidity',
    questionKey: 'support.faq.market.liquidity.q',
    answerKey: 'support.faq.market.liquidity.a',
    tags: ['liquidität', 'liquidity', 'volume'],
    followUpId: 'market-liquidity-fu',},
  {
    id: 'profit-earn',
    questionKey: 'support.faq.profit.earn.q',
    answerKey: 'support.faq.profit.earn.a',
    tags: ['geld', 'verdienen', 'profit'],
    followUpId: 'profit-earn-fu',},
  {
    id: 'profit-longterm',
    questionKey: 'support.faq.profit.longterm.q',
    answerKey: 'support.faq.profit.longterm.a',
    tags: ['langfristig', 'chance', 'winrate'],
    followUpId: 'profit-longterm-fu',},
  {
    id: 'profit-roi',
    questionKey: 'support.faq.profit.roi.q',
    answerKey: 'support.faq.profit.roi.a',
    tags: ['roi', 'realistisch'],
    followUpId: 'profit-roi-fu',},
  {
    id: 'profit-timeToProfit',
    questionKey: 'support.faq.profit.timeToProfit.q',
    answerKey: 'support.faq.profit.timeToProfit.a',
    tags: ['dauer', 'profitabel', 'zeit'],
    followUpId: 'profit-timeToProfit-fu',},
  {
    id: 'profit-capital',
    questionKey: 'support.faq.profit.capital.q',
    answerKey: 'support.faq.profit.capital.a',
    tags: ['kapital', 'bankroll', 'startgeld'],
    followUpId: 'profit-capital-fu',},
  {
    id: 'profit-skillVsLuck',
    questionKey: 'support.faq.profit.skillVsLuck.q',
    answerKey: 'support.faq.profit.skillVsLuck.a',
    tags: ['skill', 'glück', 'luck'],
    followUpId: 'profit-skillVsLuck-fu',},
  {
    id: 'profit-prosVsAmateurs',
    questionKey: 'support.faq.profit.prosVsAmateurs.q',
    answerKey: 'support.faq.profit.prosVsAmateurs.a',
    tags: ['profi', 'amateur', 'unterschied'],
    followUpId: 'profit-prosVsAmateurs-fu',},
  {
    id: 'profit-prosWork',
    questionKey: 'support.faq.profit.prosWork.q',
    answerKey: 'support.faq.profit.prosWork.a',
    tags: ['profi', 'arbeit', 'routine'],
    followUpId: 'profit-prosWork-fu',},
  {
    id: 'profit-patience',
    questionKey: 'support.faq.profit.patience.q',
    answerKey: 'support.faq.profit.patience.a',
    tags: ['geduld', 'patience'],
    followUpId: 'profit-patience-fu',},
  {
    id: 'profit-fail90',
    questionKey: 'support.faq.profit.fail90.q',
    answerKey: 'support.faq.profit.fail90.a',
    tags: ['scheitern', '90', 'verlieren'],
    followUpId: 'profit-fail90-fu',},
  {
    id: 'platform-daily',
    questionKey: 'support.faq.platform.daily.q',
    answerKey: 'support.faq.platform.daily.a',
    tags: ['täglich', 'daily', 'prediction'],
    followUpId: 'platform-daily-fu',},
  {
    id: 'platform-autoload',
    questionKey: 'support.faq.platform.autoload.q',
    answerKey: 'support.faq.platform.autoload.a',
    tags: ['spiele', 'laden', 'api'],
    followUpId: 'platform-autoload-fu',},
  {
    id: 'platform-updateFreq',
    questionKey: 'support.faq.platform.updateFreq.q',
    answerKey: 'support.faq.platform.updateFreq.a',
    tags: ['update', 'frequenz', 'häufig'],
    followUpId: 'platform-updateFreq-fu',},
  {
    id: 'platform-confidence',
    questionKey: 'support.faq.platform.confidence.q',
    answerKey: 'support.faq.platform.confidence.a',
    tags: ['confidence', 'score'],
    followUpId: 'platform-confidence-fu',},
  {
    id: 'platform-visualize',
    questionKey: 'support.faq.platform.visualize.q',
    answerKey: 'support.faq.platform.visualize.a',
    tags: ['visualisieren', 'visualize', 'chart'],
    followUpId: 'platform-visualize-fu',},
  {
    id: 'platform-bestbets',
    questionKey: 'support.faq.platform.bestBets.q',
    answerKey: 'support.faq.platform.bestBets.a',
    tags: ['beste', 'wetten', 'filter'],
    followUpId: 'platform-bestbets-fu',},
  {
    id: 'platform-history',
    questionKey: 'support.faq.platform.history.q',
    answerKey: 'support.faq.platform.history.a',
    tags: ['historisch', 'performance', 'track'],
    followUpId: 'platform-history-fu',},
  {
    id: 'platform-tracking',
    questionKey: 'support.faq.platform.tracking.q',
    answerKey: 'support.faq.platform.tracking.a',
    tags: ['user', 'tracking', 'analytics'],
    followUpId: 'platform-tracking-fu',},
  {
    id: 'platform-ranking',
    questionKey: 'support.faq.platform.ranking.q',
    answerKey: 'support.faq.platform.ranking.a',
    tags: ['ranking', 'tipps', 'rank'],
    followUpId: 'platform-ranking-fu',},
  {
    id: 'platform-lastBets',
    questionKey: 'support.faq.platform.lastBets.q',
    answerKey: 'support.faq.platform.lastBets.a',
    tags: ['letzte', 'bets', 'recent'],
    followUpId: 'platform-lastBets-fu',},
  {
    id: 'platform-wrongMatch',
    questionKey: 'support.faq.platform.wrongMatch.q',
    answerKey: 'support.faq.platform.wrongMatch.a',
    tags: ['falsch', 'spiele', 'bug'],
    followUpId: 'platform-wrongMatch-fu',},
  {
    id: 'platform-valueVsPrediction',
    questionKey: 'support.faq.platform.valueVsPrediction.q',
    answerKey: 'support.faq.platform.valueVsPrediction.a',
    tags: ['value', 'prediction', 'unterschied'],
    followUpId: 'platform-valueVsPrediction-fu',},
  {
    id: 'platform-alerts',
    questionKey: 'support.faq.platform.alerts.q',
    answerKey: 'support.faq.platform.alerts.a',
    tags: ['alert', 'notification', 'benachrichtigung'],
    followUpId: 'platform-alerts-fu',},
  {
    id: 'platform-trust',
    questionKey: 'support.faq.platform.trust.q',
    answerKey: 'support.faq.platform.trust.a',
    tags: ['vertrauen', 'trust', 'transparenz'],
    followUpId: 'platform-trust-fu',},


  // <BEGIN_FOLLOWUP_ENTRIES>
  {
    id: 'value-bet-fu',
    questionKey: 'support.faq.valueBet.fq',
    answerKey: 'support.faq.valueBet.fa',
    tags: ['bet', 'deep', 'edge', 'follow', 'kelly', 'odds', 'practice', 'praxis', 'quote', 'value', 'wert', 'wette'],
  },
  {
    id: 'accuracy-fu',
    questionKey: 'support.faq.accuracy.fq',
    answerKey: 'support.faq.accuracy.fa',
    tags: ['accuracy', 'brier', 'deep', 'follow', 'genauigkeit', 'model', 'modell', 'practice', 'praxis', 'prediction', 'rps', 'vorhersage'],
  },
  {
    id: 'data-source-fu',
    questionKey: 'support.faq.dataSource.fq',
    answerKey: 'support.faq.dataSource.fa',
    tags: ['data', 'daten', 'deep', 'follow', 'football-data', 'odds', 'practice', 'praxis', 'quelle', 'sofascore', 'source'],
  },
  {
    id: 'snapshot-update-fu',
    questionKey: 'support.faq.snapshotUpdate.fq',
    answerKey: 'support.faq.snapshotUpdate.fa',
    tags: ['aktualisierung', 'deep', 'follow', 'practice', 'praxis', 'refresh', 'snapshot', 'time', 'update', 'wann', 'zeit'],
  },
  {
    id: 'kelly-fu',
    questionKey: 'support.faq.kelly.fq',
    answerKey: 'support.faq.kelly.fa',
    tags: ['bankroll', 'deep', 'einsatz', 'follow', 'kelly', 'practice', 'praxis', 'risiko', 'risk', 'stake', 'staking'],
  },
  {
    id: 'pi-rating-fu',
    questionKey: 'support.faq.piRating.fq',
    answerKey: 'support.faq.piRating.fa',
    tags: ['deep', 'elo', 'follow', 'pi', 'practice', 'praxis', 'rating', 'staerke', 'strength', 'stärke', 'team'],
  },
  {
    id: 'responsible-fu',
    questionKey: 'support.faq.responsible.fq',
    answerKey: 'support.faq.responsible.fa',
    tags: ['advice', 'beratung', 'deep', 'financial', 'follow', 'gambling', 'practice', 'praxis', 'responsible', 'spielsucht', 'verantwortung'],
  },
  {
    id: 'language-fu',
    questionKey: 'support.faq.language.fq',
    answerKey: 'support.faq.language.fa',
    tags: ['deep', 'follow', 'language', 'locale', 'practice', 'praxis', 'sprache', 'translation', 'übersetzung'],
  },
  {
    id: 'cookies-fu',
    questionKey: 'support.faq.cookies.fq',
    answerKey: 'support.faq.cookies.fa',
    tags: ['consent', 'cookie', 'cookies', 'datenschutz', 'deep', 'einwilligung', 'follow', 'practice', 'praxis', 'privacy'],
  },
  {
    id: 'contact-fu',
    questionKey: 'support.faq.contact.fq',
    answerKey: 'support.faq.contact.fa',
    tags: ['contact', 'deep', 'email', 'follow', 'help', 'hilfe', 'kontakt', 'practice', 'praxis', 'support'],
  },
  {
    id: 'basics-1x2-fu',
    questionKey: 'support.faq.basics.oneX2.fq',
    answerKey: 'support.faq.basics.oneX2.fa',
    tags: ['1x2', 'auswärts', 'away', 'draw', 'heim', 'home', 'market', 'markt', 'practice', 'praxis', 'unentschieden', 'wann', 'when'],
  },
  {
    id: 'basics-odds-fu',
    questionKey: 'support.faq.basics.odds.fq',
    answerKey: 'support.faq.basics.odds.fa',
    tags: ['cote', 'cuota', 'decimal', 'dezimal', 'odds', 'practice', 'praxis', 'quote', 'quoten', 'wann', 'when'],
  },
  {
    id: 'basics-winnings-fu',
    questionKey: 'support.faq.basics.winnings.fq',
    answerKey: 'support.faq.basics.winnings.fa',
    tags: ['auszahlung', 'berechnen', 'calculate', 'gewinn', 'payout', 'practice', 'praxis', 'profit', 'wann', 'when'],
  },
  {
    id: 'basics-single-fu',
    questionKey: 'support.faq.basics.single.fq',
    answerKey: 'support.faq.basics.single.fa',
    tags: ['einzel', 'einzelwette', 'practice', 'praxis', 'single', 'wann', 'when'],
  },
  {
    id: 'basics-accumulator-fu',
    questionKey: 'support.faq.basics.accumulator.fq',
    answerKey: 'support.faq.basics.accumulator.fa',
    tags: ['accumulator', 'combo', 'kombi', 'kombiwette', 'parlay', 'practice', 'praxis', 'wann', 'when'],
  },
  {
    id: 'basics-system-fu',
    questionKey: 'support.faq.basics.system.fq',
    answerKey: 'support.faq.basics.system.fa',
    tags: ['practice', 'praxis', 'system', 'systemwette', 'wann', 'when'],
  },
  {
    id: 'basics-valuebet-fu',
    questionKey: 'support.faq.basics.valueBetBasic.fq',
    answerKey: 'support.faq.basics.valueBetBasic.fa',
    tags: ['+ev', 'edge', 'practice', 'praxis', 'value', 'wann', 'wert', 'when'],
  },
  {
    id: 'basics-probability-fu',
    questionKey: 'support.faq.basics.probability.fq',
    answerKey: 'support.faq.basics.probability.fa',
    tags: ['implied', 'implizit', 'practice', 'praxis', 'probability', 'wahrscheinlichkeit', 'wann', 'when'],
  },
  {
    id: 'basics-bookie-fu',
    questionKey: 'support.faq.basics.bookie.fq',
    answerKey: 'support.faq.basics.bookie.fa',
    tags: ['anbieter', 'bookie', 'bookmaker', 'buchmacher', 'practice', 'praxis', 'wann', 'when'],
  },
  {
    id: 'basics-bookiemoney-fu',
    questionKey: 'support.faq.basics.bookieMoney.fq',
    answerKey: 'support.faq.basics.bookieMoney.fa',
    tags: ['bookmaker', 'marge', 'overround', 'practice', 'praxis', 'profit', 'vig', 'wann', 'when'],
  },
  {
    id: 'basics-overround-fu',
    questionKey: 'support.faq.basics.overround.fq',
    answerKey: 'support.faq.basics.overround.fa',
    tags: ['juice', 'marge', 'margin', 'overround', 'practice', 'praxis', 'vig', 'wann', 'when'],
  },
  {
    id: 'basics-live-fu',
    questionKey: 'support.faq.basics.live.fq',
    answerKey: 'support.faq.basics.live.fa',
    tags: ['in-play', 'live', 'livewette', 'practice', 'praxis', 'wann', 'when'],
  },
  {
    id: 'basics-cashout-fu',
    questionKey: 'support.faq.basics.cashout.fq',
    answerKey: 'support.faq.basics.cashout.fa',
    tags: ['auszahlen', 'cash-out', 'cashout', 'practice', 'praxis', 'wann', 'when'],
  },
  {
    id: 'basics-handicap-fu',
    questionKey: 'support.faq.basics.handicap.fq',
    answerKey: 'support.faq.basics.handicap.fa',
    tags: ['asian', 'asiatisch', 'handicap', 'practice', 'praxis', 'spread', 'wann', 'when'],
  },
  {
    id: 'basics-asianhandicap-fu',
    questionKey: 'support.faq.basics.asianHandicap.fq',
    answerKey: 'support.faq.basics.asianHandicap.fa',
    tags: ['asian', 'halb', 'handicap', 'practice', 'praxis', 'viertel', 'wann', 'when'],
  },
  {
    id: 'basics-ou25-fu',
    questionKey: 'support.faq.basics.ou25.fq',
    answerKey: 'support.faq.basics.ou25.fa',
    tags: ['2.5', 'goals', 'over', 'practice', 'praxis', 'tore', 'totale', 'under', 'wann', 'when'],
  },
  {
    id: 'basics-btts-fu',
    questionKey: 'support.faq.basics.btts.fq',
    answerKey: 'support.faq.basics.btts.fa',
    tags: ['both', 'btts', 'practice', 'praxis', 'score', 'teams', 'tor', 'wann', 'when'],
  },
  {
    id: 'basics-dnb-fu',
    questionKey: 'support.faq.basics.dnb.fq',
    answerKey: 'support.faq.basics.dnb.fa',
    tags: ['bet', 'dnb', 'draw', 'no', 'practice', 'praxis', 'remis', 'wann', 'when'],
  },
  {
    id: 'basics-doublechance-fu',
    questionKey: 'support.faq.basics.doubleChance.fq',
    answerKey: 'support.faq.basics.doubleChance.fa',
    tags: ['chance', 'doppelt', 'double', 'practice', 'praxis', 'wann', 'when'],
  },
  {
    id: 'basics-specials-fu',
    questionKey: 'support.faq.basics.specials.fq',
    answerKey: 'support.faq.basics.specials.fa',
    tags: ['practice', 'praxis', 'scorer', 'special', 'spezial', 'torschütze', 'wann', 'when'],
  },
  {
    id: 'analysis-howto-fu',
    questionKey: 'support.faq.analysis.howTo.fq',
    answerKey: 'support.faq.analysis.howTo.fa',
    tags: ['analyse', 'analyze', 'gewicht', 'match', 'signale', 'signals', 'spiel', 'weight'],
  },
  {
    id: 'analysis-stats-fu',
    questionKey: 'support.faq.analysis.stats.fq',
    answerKey: 'support.faq.analysis.stats.fa',
    tags: ['gewicht', 'schüsse', 'shots', 'signale', 'signals', 'statistik', 'stats', 'weight', 'xg'],
  },
  {
    id: 'analysis-form-fu',
    questionKey: 'support.faq.analysis.form.fq',
    answerKey: 'support.faq.analysis.form.fa',
    tags: ['aktuell', 'form', 'gewicht', 'momentum', 'signale', 'signals', 'streak', 'weight'],
  },
  {
    id: 'analysis-homeaway-fu',
    questionKey: 'support.faq.analysis.homeAway.fq',
    answerKey: 'support.faq.analysis.homeAway.fa',
    tags: ['advantage', 'auswärts', 'away', 'gewicht', 'heim', 'home', 'signale', 'signals', 'weight'],
  },
  {
    id: 'analysis-injuries-fu',
    questionKey: 'support.faq.analysis.injuries.fq',
    answerKey: 'support.faq.analysis.injuries.fa',
    tags: ['ausfall', 'gewicht', 'injury', 'signale', 'signals', 'sperre', 'verletzung', 'weight'],
  },
  {
    id: 'analysis-lineups-fu',
    questionKey: 'support.faq.analysis.lineups.fq',
    answerKey: 'support.faq.analysis.lineups.fa',
    tags: ['aufstellung', 'gewicht', 'lineup', 'signale', 'signals', 'starting', 'weight'],
  },
  {
    id: 'analysis-xg-fu',
    questionKey: 'support.faq.analysis.xg.fq',
    answerKey: 'support.faq.analysis.xg.fa',
    tags: ['expected', 'gewicht', 'goals', 'signale', 'signals', 'weight', 'xg'],
  },
  {
    id: 'analysis-h2h-fu',
    questionKey: 'support.faq.analysis.h2h.fq',
    answerKey: 'support.faq.analysis.h2h.fa',
    tags: ['direkt', 'gewicht', 'h2h', 'head-to-head', 'signale', 'signals', 'weight'],
  },
  {
    id: 'analysis-motivation-fu',
    questionKey: 'support.faq.analysis.motivation.fq',
    answerKey: 'support.faq.analysis.motivation.fa',
    tags: ['abstieg', 'gewicht', 'motivation', 'pokal', 'signale', 'signals', 'titel', 'weight'],
  },
  {
    id: 'analysis-weather-fu',
    questionKey: 'support.faq.analysis.weather.fq',
    answerKey: 'support.faq.analysis.weather.fa',
    tags: ['gewicht', 'regen', 'signale', 'signals', 'weather', 'weight', 'wetter', 'wind'],
  },
  {
    id: 'analysis-deffoff-fu',
    questionKey: 'support.faq.analysis.defOff.fq',
    answerKey: 'support.faq.analysis.defOff.fa',
    tags: ['defense', 'defensiv', 'gewicht', 'offense', 'offensiv', 'signale', 'signals', 'weight'],
  },
  {
    id: 'analysis-goalstats-fu',
    questionKey: 'support.faq.analysis.goalStats.fq',
    answerKey: 'support.faq.analysis.goalStats.fa',
    tags: ['gewicht', 'goals', 'signale', 'signals', 'tore', 'torstatistik', 'weight'],
  },
  {
    id: 'analysis-bestleague-fu',
    questionKey: 'support.faq.analysis.bestLeague.fq',
    answerKey: 'support.faq.analysis.bestLeague.fa',
    tags: ['gewicht', 'league', 'liga', 'signale', 'signals', 'vorhersagbar', 'weight'],
  },
  {
    id: 'analysis-coach-fu',
    questionKey: 'support.faq.analysis.coach.fq',
    answerKey: 'support.faq.analysis.coach.fa',
    tags: ['coach', 'gewicht', 'signale', 'signals', 'trainer', 'wechsel', 'weight'],
  },
  {
    id: 'analysis-tempo-fu',
    questionKey: 'support.faq.analysis.tempo.fq',
    answerKey: 'support.faq.analysis.tempo.fa',
    tags: ['gewicht', 'pace', 'signale', 'signals', 'tactics', 'taktik', 'tempo', 'weight'],
  },
  {
    id: 'analysis-ougames-fu',
    questionKey: 'support.faq.analysis.ouGames.fq',
    answerKey: 'support.faq.analysis.ouGames.fa',
    tags: ['gewicht', 'ou', 'over', 'signale', 'signals', 'tore', 'under', 'weight'],
  },
  {
    id: 'analysis-bttsgames-fu',
    questionKey: 'support.faq.analysis.bttsGames.fq',
    answerKey: 'support.faq.analysis.bttsGames.fa',
    tags: ['both', 'btts', 'gewicht', 'score', 'signale', 'signals', 'weight'],
  },
  {
    id: 'analysis-draws-fu',
    questionKey: 'support.faq.analysis.draws.fq',
    answerKey: 'support.faq.analysis.draws.fa',
    tags: ['draw', 'gewicht', 'remis', 'signale', 'signals', 'unentschieden', 'weight'],
  },
  {
    id: 'analysis-underdogs-fu',
    questionKey: 'support.faq.analysis.underdogs.fq',
    answerKey: 'support.faq.analysis.underdogs.fa',
    tags: ['außenseiter', 'gewicht', 'outsider', 'signale', 'signals', 'underdog', 'weight'],
  },
  {
    id: 'analysis-trapgames-fu',
    questionKey: 'support.faq.analysis.trapGames.fq',
    answerKey: 'support.faq.analysis.trapGames.fa',
    tags: ['cup', 'falle', 'gewicht', 'rotation', 'signale', 'signals', 'trap', 'weight'],
  },
  {
    id: 'strategy-best-fu',
    questionKey: 'support.faq.strategy.best.fq',
    answerKey: 'support.faq.strategy.best.fa',
    tags: ['best', 'beste', 'discipline', 'execute', 'practice', 'praxis', 'strategie', 'strategy'],
  },
  {
    id: 'strategy-value-fu',
    questionKey: 'support.faq.strategy.valueBet.fq',
    answerKey: 'support.faq.strategy.valueBet.fa',
    tags: ['betting', 'discipline', 'edge', 'execute', 'practice', 'praxis', 'value'],
  },
  {
    id: 'strategy-arbitrage-fu',
    questionKey: 'support.faq.strategy.arbitrage.fq',
    answerKey: 'support.faq.strategy.arbitrage.fa',
    tags: ['arbitrage', 'discipline', 'execute', 'practice', 'praxis', 'surebet'],
  },
  {
    id: 'strategy-martingale-fu',
    questionKey: 'support.faq.strategy.martingale.fq',
    answerKey: 'support.faq.strategy.martingale.fa',
    tags: ['discipline', 'doubling', 'execute', 'martingale', 'practice', 'praxis', 'progression'],
  },
  {
    id: 'strategy-flat-fu',
    questionKey: 'support.faq.strategy.flat.fq',
    answerKey: 'support.faq.strategy.flat.fa',
    tags: ['discipline', 'execute', 'flat', 'practice', 'praxis', 'staking'],
  },
  {
    id: 'strategy-bankroll-fu',
    questionKey: 'support.faq.strategy.bankroll.fq',
    answerKey: 'support.faq.strategy.bankroll.fa',
    tags: ['bankroll', 'discipline', 'execute', 'kapital', 'management', 'practice', 'praxis'],
  },
  {
    id: 'strategy-stake-fu',
    questionKey: 'support.faq.strategy.stake.fq',
    answerKey: 'support.faq.strategy.stake.fa',
    tags: ['discipline', 'einsatz', 'execute', 'practice', 'praxis', 'size', 'stake'],
  },
  {
    id: 'strategy-losingstreak-fu',
    questionKey: 'support.faq.strategy.losingStreak.fq',
    answerKey: 'support.faq.strategy.losingStreak.fa',
    tags: ['discipline', 'drawdown', 'execute', 'practice', 'praxis', 'streak', 'verlust'],
  },
  {
    id: 'strategy-combos-fu',
    questionKey: 'support.faq.strategy.combos.fq',
    answerKey: 'support.faq.strategy.combos.fa',
    tags: ['combo', 'discipline', 'execute', 'kombi', 'parlay', 'practice', 'praxis'],
  },
  {
    id: 'strategy-profitable-fu',
    questionKey: 'support.faq.strategy.profitable.fq',
    answerKey: 'support.faq.strategy.profitable.fa',
    tags: ['discipline', 'execute', 'langfristig', 'long-term', 'practice', 'praxis', 'profitabel'],
  },
  {
    id: 'strategy-test-fu',
    questionKey: 'support.faq.strategy.test.fq',
    answerKey: 'support.faq.strategy.test.fa',
    tags: ['backtest', 'discipline', 'execute', 'practice', 'praxis', 'test', 'validieren'],
  },
  {
    id: 'strategy-roi-fu',
    questionKey: 'support.faq.strategy.roi.fq',
    answerKey: 'support.faq.strategy.roi.fa',
    tags: ['discipline', 'execute', 'investment', 'practice', 'praxis', 'return', 'roi'],
  },
  {
    id: 'strategy-strikerate-fu',
    questionKey: 'support.faq.strategy.strikeRate.fq',
    answerKey: 'support.faq.strategy.strikeRate.fa',
    tags: ['discipline', 'execute', 'practice', 'praxis', 'rate', 'strike', 'trefferquote'],
  },
  {
    id: 'strategy-discipline-fu',
    questionKey: 'support.faq.strategy.discipline.fq',
    answerKey: 'support.faq.strategy.discipline.fa',
    tags: ['discipline', 'disziplin', 'execute', 'practice', 'praxis'],
  },
  {
    id: 'strategy-goododds-fu',
    questionKey: 'support.faq.strategy.goodOdds.fq',
    answerKey: 'support.faq.strategy.goodOdds.fa',
    tags: ['discipline', 'execute', 'gute', 'odds', 'practice', 'praxis', 'quote', 'schlechte'],
  },
  {
    id: 'strategy-nobet-fu',
    questionKey: 'support.faq.strategy.noBet.fq',
    answerKey: 'support.faq.strategy.noBet.fa',
    tags: ['discipline', 'execute', 'nicht', 'practice', 'praxis', 'skip', 'wetten'],
  },
  {
    id: 'strategy-timing-fu',
    questionKey: 'support.faq.strategy.timing.fq',
    answerKey: 'support.faq.strategy.timing.fa',
    tags: ['discipline', 'execute', 'practice', 'praxis', 'timing', 'wann', 'when'],
  },
  {
    id: 'strategy-prematchlive-fu',
    questionKey: 'support.faq.strategy.prematchLive.fq',
    answerKey: 'support.faq.strategy.prematchLive.fa',
    tags: ['discipline', 'execute', 'in-play', 'live', 'practice', 'praxis', 'pre-match'],
  },
  {
    id: 'strategy-oddsmovement-fu',
    questionKey: 'support.faq.strategy.oddsMovement.fq',
    answerKey: 'support.faq.strategy.oddsMovement.fa',
    tags: ['discipline', 'drift', 'execute', 'movement', 'odds', 'practice', 'praxis'],
  },
  {
    id: 'strategy-ownsystem-fu',
    questionKey: 'support.faq.strategy.ownSystem.fq',
    answerKey: 'support.faq.strategy.ownSystem.fa',
    tags: ['custom', 'discipline', 'eigenes', 'execute', 'practice', 'praxis', 'system'],
  },
  {
    id: 'mistakes-losemoney-fu',
    questionKey: 'support.faq.mistakes.loseMoney.fq',
    answerKey: 'support.faq.mistakes.loseMoney.fa',
    tags: ['avoid', 'guardrail', 'lose', 'money', 'verlieren', 'vermeiden'],
  },
  {
    id: 'mistakes-chasing-fu',
    questionKey: 'support.faq.mistakes.chasing.fq',
    answerKey: 'support.faq.mistakes.chasing.fa',
    tags: ['avoid', 'chasing', 'guardrail', 'losses', 'verlust', 'vermeiden'],
  },
  {
    id: 'mistakes-emotions-fu',
    questionKey: 'support.faq.mistakes.emotions.fq',
    answerKey: 'support.faq.mistakes.emotions.fa',
    tags: ['avoid', 'emotion', 'guardrail', 'tilt', 'vermeiden'],
  },
  {
    id: 'mistakes-accumulators-fu',
    questionKey: 'support.faq.mistakes.accumulators.fq',
    answerKey: 'support.faq.mistakes.accumulators.fa',
    tags: ['accumulator', 'avoid', 'guardrail', 'kombi', 'riskant', 'vermeiden'],
  },
  {
    id: 'mistakes-overbetting-fu',
    questionKey: 'support.faq.mistakes.overbetting.fq',
    answerKey: 'support.faq.mistakes.overbetting.fa',
    tags: ['avoid', 'guardrail', 'over', 'overbetting', 'stake', 'vermeiden'],
  },
  {
    id: 'mistakes-tipsters-fu',
    questionKey: 'support.faq.mistakes.tipsters.fq',
    answerKey: 'support.faq.mistakes.tipsters.fa',
    tags: ['avoid', 'blind', 'experte', 'guardrail', 'tipster', 'vermeiden'],
  },
  {
    id: 'mistakes-nobankroll-fu',
    questionKey: 'support.faq.mistakes.noBankroll.fq',
    answerKey: 'support.faq.mistakes.noBankroll.fa',
    tags: ['avoid', 'bankroll', 'fail', 'guardrail', 'no', 'vermeiden'],
  },
  {
    id: 'mistakes-surebets-fu',
    questionKey: 'support.faq.mistakes.sureBets.fq',
    answerKey: 'support.faq.mistakes.sureBets.fa',
    tags: ['avoid', 'guardrail', 'sichere', 'sure', 'tipps', 'vermeiden'],
  },
  {
    id: 'mistakes-favteam-fu',
    questionKey: 'support.faq.mistakes.favTeam.fq',
    answerKey: 'support.faq.mistakes.favTeam.fa',
    tags: ['avoid', 'bias', 'fav', 'guardrail', 'lieblings', 'vermeiden'],
  },
  {
    id: 'mistakes-beginner-fu',
    questionKey: 'support.faq.mistakes.beginner.fq',
    answerKey: 'support.faq.mistakes.beginner.fa',
    tags: ['anfänger', 'avoid', 'beginner', 'fehler', 'guardrail', 'vermeiden'],
  },
  {
    id: 'ai-how-fu',
    questionKey: 'support.faq.ai.how.fq',
    answerKey: 'support.faq.ai.how.fa',
    tags: ['ai', 'grenze', 'ki', 'limit', 'limits', 'prediction', 'prognose'],
  },
  {
    id: 'ai-data-fu',
    questionKey: 'support.faq.ai.data.fq',
    answerKey: 'support.faq.ai.data.fa',
    tags: ['data', 'daten', 'features', 'grenze', 'limit', 'limits'],
  },
  {
    id: 'ai-reliability-fu',
    questionKey: 'support.faq.ai.reliability.fq',
    answerKey: 'support.faq.ai.reliability.fa',
    tags: ['accuracy', 'grenze', 'limit', 'limits', 'reliable', 'zuverlässig'],
  },
  {
    id: 'ai-model-fu',
    questionKey: 'support.faq.ai.model.fq',
    answerKey: 'support.faq.ai.model.fa',
    tags: ['grenze', 'limit', 'limits', 'model', 'modell', 'prediction'],
  },
  {
    id: 'ai-ml-fu',
    questionKey: 'support.faq.ai.ml.fq',
    answerKey: 'support.faq.ai.ml.fa',
    tags: ['grenze', 'learning', 'limit', 'limits', 'machine', 'ml'],
  },
  {
    id: 'ai-features-fu',
    questionKey: 'support.faq.ai.features.fq',
    answerKey: 'support.faq.ai.features.fa',
    tags: ['features', 'grenze', 'limit', 'limits', 'variablen'],
  },
  {
    id: 'ai-history-fu',
    questionKey: 'support.faq.ai.history.fq',
    answerKey: 'support.faq.ai.history.fa',
    tags: ['daten', 'grenze', 'historisch', 'history', 'limit', 'limits'],
  },
  {
    id: 'ai-oddsmodel-fu',
    questionKey: 'support.faq.ai.oddsModel.fq',
    answerKey: 'support.faq.ai.oddsModel.fa',
    tags: ['grenze', 'limit', 'limits', 'model', 'odds', 'quote'],
  },
  {
    id: 'ai-valuebet-fu',
    questionKey: 'support.faq.ai.valueBet.fq',
    answerKey: 'support.faq.ai.valueBet.fa',
    tags: ['edge', 'grenze', 'ki', 'limit', 'limits', 'value'],
  },
  {
    id: 'ai-overfitting-fu',
    questionKey: 'support.faq.ai.overfitting.fq',
    answerKey: 'support.faq.ai.overfitting.fa',
    tags: ['grenze', 'limit', 'limits', 'overfitting', 'regulation'],
  },
  {
    id: 'ai-algorithms-fu',
    questionKey: 'support.faq.ai.algorithms.fq',
    answerKey: 'support.faq.ai.algorithms.fa',
    tags: ['algorithm', 'catboost', 'grenze', 'limit', 'limits', 'randomforest'],
  },
  {
    id: 'ai-livedata-fu',
    questionKey: 'support.faq.ai.liveData.fq',
    answerKey: 'support.faq.ai.liveData.fa',
    tags: ['daten', 'echtzeit', 'grenze', 'limit', 'limits', 'live'],
  },
  {
    id: 'ai-realtime-fu',
    questionKey: 'support.faq.ai.realtime.fq',
    answerKey: 'support.faq.ai.realtime.fa',
    tags: ['echtzeit', 'grenze', 'limit', 'limits', 'realtime', 'update'],
  },
  {
    id: 'ai-measure-fu',
    questionKey: 'support.faq.ai.measure.fq',
    answerKey: 'support.faq.ai.measure.fa',
    tags: ['accuracy', 'genauigkeit', 'grenze', 'limit', 'limits', 'metric'],
  },
  {
    id: 'ai-improve-fu',
    questionKey: 'support.faq.ai.improve.fq',
    answerKey: 'support.faq.ai.improve.fa',
    tags: ['grenze', 'improve', 'limit', 'limits', 'model', 'verbessern'],
  },
  {
    id: 'ai-combine-fu',
    questionKey: 'support.faq.ai.combine.fq',
    answerKey: 'support.faq.ai.combine.fa',
    tags: ['combine', 'ensemble', 'grenze', 'kombinieren', 'limit', 'limits'],
  },
  {
    id: 'ai-ensemble-fu',
    questionKey: 'support.faq.ai.ensemble.fq',
    answerKey: 'support.faq.ai.ensemble.fa',
    tags: ['betting', 'ensemble', 'grenze', 'limit', 'limits', 'stacking'],
  },
  {
    id: 'ai-apis-fu',
    questionKey: 'support.faq.ai.apis.fq',
    answerKey: 'support.faq.ai.apis.fa',
    tags: ['api', 'daten', 'feed', 'grenze', 'limit', 'limits'],
  },
  {
    id: 'ai-dashboard-fu',
    questionKey: 'support.faq.ai.dashboard.fq',
    answerKey: 'support.faq.ai.dashboard.fa',
    tags: ['dashboard', 'grenze', 'limit', 'limits', 'ui', 'visualisierung'],
  },
  {
    id: 'ai-automate-fu',
    questionKey: 'support.faq.ai.automate.fq',
    answerKey: 'support.faq.ai.automate.fa',
    tags: ['automate', 'automatisieren', 'cron', 'grenze', 'limit', 'limits'],
  },
  {
    id: 'market-create-fu',
    questionKey: 'support.faq.market.create.fq',
    answerKey: 'support.faq.market.create.fa',
    tags: ['closing', 'clv', 'entstehen', 'odds', 'quoten', 'use'],
  },
  {
    id: 'market-change-fu',
    questionKey: 'support.faq.market.change.fq',
    answerKey: 'support.faq.market.change.fa',
    tags: ['change', 'closing', 'clv', 'move', 'use', 'ändern'],
  },
  {
    id: 'market-clv-fu',
    questionKey: 'support.faq.market.clv.fq',
    answerKey: 'support.faq.market.clv.fa',
    tags: ['closing', 'clv', 'line', 'use', 'value'],
  },
  {
    id: 'market-valueOdds-fu',
    questionKey: 'support.faq.market.valueOdds.fq',
    answerKey: 'support.faq.market.valueOdds.fa',
    tags: ['closing', 'clv', 'erkennen', 'quote', 'use', 'value'],
  },
  {
    id: 'market-bestbooks-fu',
    questionKey: 'support.faq.market.bestBooks.fq',
    answerKey: 'support.faq.market.bestBooks.fa',
    tags: ['beste', 'bookmaker', 'buchmacher', 'closing', 'clv', 'use'],
  },
  {
    id: 'market-diffbooks-fu',
    questionKey: 'support.faq.market.diffBooks.fq',
    answerKey: 'support.faq.market.diffBooks.fa',
    tags: ['bookmaker', 'closing', 'clv', 'diff', 'unterschied', 'use'],
  },
  {
    id: 'market-compare-fu',
    questionKey: 'support.faq.market.compare.fq',
    answerKey: 'support.faq.market.compare.fa',
    tags: ['closing', 'clv', 'compare', 'odds', 'use', 'vergleich'],
  },
  {
    id: 'market-sharppublic-fu',
    questionKey: 'support.faq.market.sharpPublic.fq',
    answerKey: 'support.faq.market.sharpPublic.fa',
    tags: ['closing', 'clv', 'money', 'public', 'sharp', 'use'],
  },
  {
    id: 'market-movement-fu',
    questionKey: 'support.faq.market.movement.fq',
    answerKey: 'support.faq.market.movement.fa',
    tags: ['bewegung', 'closing', 'clv', 'drift', 'movement', 'use'],
  },
  {
    id: 'market-liquidity-fu',
    questionKey: 'support.faq.market.liquidity.fq',
    answerKey: 'support.faq.market.liquidity.fa',
    tags: ['closing', 'clv', 'liquidity', 'liquidität', 'use', 'volume'],
  },
  {
    id: 'profit-earn-fu',
    questionKey: 'support.faq.profit.earn.fq',
    answerKey: 'support.faq.profit.earn.fa',
    tags: ['expectation', 'geld', 'profit', 'realistic', 'realistisch', 'verdienen'],
  },
  {
    id: 'profit-longterm-fu',
    questionKey: 'support.faq.profit.longterm.fq',
    answerKey: 'support.faq.profit.longterm.fa',
    tags: ['chance', 'expectation', 'langfristig', 'realistic', 'realistisch', 'winrate'],
  },
  {
    id: 'profit-roi-fu',
    questionKey: 'support.faq.profit.roi.fq',
    answerKey: 'support.faq.profit.roi.fa',
    tags: ['expectation', 'realistic', 'realistisch', 'roi'],
  },
  {
    id: 'profit-timeToProfit-fu',
    questionKey: 'support.faq.profit.timeToProfit.fq',
    answerKey: 'support.faq.profit.timeToProfit.fa',
    tags: ['dauer', 'expectation', 'profitabel', 'realistic', 'realistisch', 'zeit'],
  },
  {
    id: 'profit-capital-fu',
    questionKey: 'support.faq.profit.capital.fq',
    answerKey: 'support.faq.profit.capital.fa',
    tags: ['bankroll', 'expectation', 'kapital', 'realistic', 'realistisch', 'startgeld'],
  },
  {
    id: 'profit-skillVsLuck-fu',
    questionKey: 'support.faq.profit.skillVsLuck.fq',
    answerKey: 'support.faq.profit.skillVsLuck.fa',
    tags: ['expectation', 'glück', 'luck', 'realistic', 'realistisch', 'skill'],
  },
  {
    id: 'profit-prosVsAmateurs-fu',
    questionKey: 'support.faq.profit.prosVsAmateurs.fq',
    answerKey: 'support.faq.profit.prosVsAmateurs.fa',
    tags: ['amateur', 'expectation', 'profi', 'realistic', 'realistisch', 'unterschied'],
  },
  {
    id: 'profit-prosWork-fu',
    questionKey: 'support.faq.profit.prosWork.fq',
    answerKey: 'support.faq.profit.prosWork.fa',
    tags: ['arbeit', 'expectation', 'profi', 'realistic', 'realistisch', 'routine'],
  },
  {
    id: 'profit-patience-fu',
    questionKey: 'support.faq.profit.patience.fq',
    answerKey: 'support.faq.profit.patience.fa',
    tags: ['expectation', 'geduld', 'patience', 'realistic', 'realistisch'],
  },
  {
    id: 'profit-fail90-fu',
    questionKey: 'support.faq.profit.fail90.fq',
    answerKey: 'support.faq.profit.fail90.fa',
    tags: ['90', 'expectation', 'realistic', 'realistisch', 'scheitern', 'verlieren'],
  },
  {
    id: 'platform-daily-fu',
    questionKey: 'support.faq.platform.daily.fq',
    answerKey: 'support.faq.platform.daily.fa',
    tags: ['app', 'daily', 'prediction', 'täglich', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-autoload-fu',
    questionKey: 'support.faq.platform.autoload.fq',
    answerKey: 'support.faq.platform.autoload.fa',
    tags: ['api', 'app', 'laden', 'spiele', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-updateFreq-fu',
    questionKey: 'support.faq.platform.updateFreq.fq',
    answerKey: 'support.faq.platform.updateFreq.fa',
    tags: ['app', 'frequenz', 'häufig', 'ui', 'update', 'where', 'wo'],
  },
  {
    id: 'platform-confidence-fu',
    questionKey: 'support.faq.platform.confidence.fq',
    answerKey: 'support.faq.platform.confidence.fa',
    tags: ['app', 'confidence', 'score', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-visualize-fu',
    questionKey: 'support.faq.platform.visualize.fq',
    answerKey: 'support.faq.platform.visualize.fa',
    tags: ['app', 'chart', 'ui', 'visualisieren', 'visualize', 'where', 'wo'],
  },
  {
    id: 'platform-bestbets-fu',
    questionKey: 'support.faq.platform.bestBets.fq',
    answerKey: 'support.faq.platform.bestBets.fa',
    tags: ['app', 'beste', 'filter', 'ui', 'wetten', 'where', 'wo'],
  },
  {
    id: 'platform-history-fu',
    questionKey: 'support.faq.platform.history.fq',
    answerKey: 'support.faq.platform.history.fa',
    tags: ['app', 'historisch', 'performance', 'track', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-tracking-fu',
    questionKey: 'support.faq.platform.tracking.fq',
    answerKey: 'support.faq.platform.tracking.fa',
    tags: ['analytics', 'app', 'tracking', 'ui', 'user', 'where', 'wo'],
  },
  {
    id: 'platform-ranking-fu',
    questionKey: 'support.faq.platform.ranking.fq',
    answerKey: 'support.faq.platform.ranking.fa',
    tags: ['app', 'rank', 'ranking', 'tipps', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-lastBets-fu',
    questionKey: 'support.faq.platform.lastBets.fq',
    answerKey: 'support.faq.platform.lastBets.fa',
    tags: ['app', 'bets', 'letzte', 'recent', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-wrongMatch-fu',
    questionKey: 'support.faq.platform.wrongMatch.fq',
    answerKey: 'support.faq.platform.wrongMatch.fa',
    tags: ['app', 'bug', 'falsch', 'spiele', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-valueVsPrediction-fu',
    questionKey: 'support.faq.platform.valueVsPrediction.fq',
    answerKey: 'support.faq.platform.valueVsPrediction.fa',
    tags: ['app', 'prediction', 'ui', 'unterschied', 'value', 'where', 'wo'],
  },
  {
    id: 'platform-alerts-fu',
    questionKey: 'support.faq.platform.alerts.fq',
    answerKey: 'support.faq.platform.alerts.fa',
    tags: ['alert', 'app', 'benachrichtigung', 'notification', 'ui', 'where', 'wo'],
  },
  {
    id: 'platform-trust-fu',
    questionKey: 'support.faq.platform.trust.fq',
    answerKey: 'support.faq.platform.trust.fa',
    tags: ['app', 'transparenz', 'trust', 'ui', 'vertrauen', 'where', 'wo'],
  },
  // <END_FOLLOWUP_ENTRIES>

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
  altQuestions: string[];
  altQuestionsNorm: string[];
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
    const altQuestions = (e.altQuestionKeys ?? []).map((k) => t(k));
    return {
      id: e.id,
      question,
      questionNorm: normalizeText(question),
      altQuestions,
      altQuestionsNorm: altQuestions
        .map((a) => normalizeText(a))
        .filter(Boolean),
      tags: e.tags,
      tagsNorm: e.tags.map((tag) => normalizeText(tag)).filter(Boolean),
    };
  });

  // Vocabulary: tag tokens + question tokens from the current locale.
  const vocabSources: string[] = [];
  for (const s of searchable) {
    vocabSources.push(s.questionNorm, ...s.altQuestionsNorm, ...s.tagsNorm);
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
    for (const an of s.altQuestionsNorm) {
      for (const tok of an.split(' ')) {
        if (tok.length >= 4) tokens.add(tok);
      }
    }
    for (const tok of tokens) {
      const bucket = tagIndex.get(tok);
      if (bucket) bucket.push(s.id);
      else tagIndex.set(tok, [s.id]);
    }
  }

  const fuse = new Fuse(searchable, {
    keys: [
      { name: 'question', weight: 0.3 },
      { name: 'questionNorm', weight: 0.25 },
      { name: 'altQuestions', weight: 0.15 },
      { name: 'altQuestionsNorm', weight: 0.15 },
      { name: 'tags', weight: 0.075 },
      { name: 'tagsNorm', weight: 0.075 },
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
