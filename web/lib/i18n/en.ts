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
  | 'transparency.group.valueBets'
  | 'transparency.group.predictions'
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
  | 'predictionCard.stake'
  | 'predictionCard.noStake'
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
  | 'bankroll.series.valueBets'
  | 'bankroll.series.predictions'
  | 'bankroll.series.combined'
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
  | 'breadcrumb.home'
  | 'rail.section.explore'
  | 'rail.section.spaces'
  | 'rail.section.today'
  | 'rail.spaces.all'
  | 'rail.today.empty'
  | 'rail.today.snapshot'
  | 'rail.quick.learn'
  | 'rail.quick.trackRecord'
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
  | 'cookie.aria.dialog'
  | 'support.toggle.label'
  | 'support.panel.title'
  | 'support.panel.close'
  | 'support.input.placeholder'
  | 'support.input.send'
  | 'support.suggestions.heading'
  | 'support.reset'
  | 'support.fallback'
  | 'support.faq.valueBet.q'
  | 'support.faq.valueBet.a'
  | 'support.faq.accuracy.q'
  | 'support.faq.accuracy.a'
  | 'support.faq.dataSource.q'
  | 'support.faq.dataSource.a'
  | 'support.faq.snapshotUpdate.q'
  | 'support.faq.snapshotUpdate.a'
  | 'support.faq.kelly.q'
  | 'support.faq.kelly.a'
  | 'support.faq.piRating.q'
  | 'support.faq.piRating.a'
  | 'support.faq.responsible.q'
  | 'support.faq.responsible.a'
  | 'support.faq.language.q'
  | 'support.faq.language.a'
  | 'support.faq.cookies.q'
  | 'support.faq.cookies.a'
  | 'support.faq.contact.q'
  | 'support.faq.contact.a'
  | 'support.faq.basics.oneX2.q'
  | 'support.faq.basics.oneX2.a'
  | 'support.faq.basics.odds.q'
  | 'support.faq.basics.odds.a'
  | 'support.faq.basics.winnings.q'
  | 'support.faq.basics.winnings.a'
  | 'support.faq.basics.single.q'
  | 'support.faq.basics.single.a'
  | 'support.faq.basics.accumulator.q'
  | 'support.faq.basics.accumulator.a'
  | 'support.faq.basics.system.q'
  | 'support.faq.basics.system.a'
  | 'support.faq.basics.valueBetBasic.q'
  | 'support.faq.basics.valueBetBasic.a'
  | 'support.faq.basics.probability.q'
  | 'support.faq.basics.probability.a'
  | 'support.faq.basics.bookie.q'
  | 'support.faq.basics.bookie.a'
  | 'support.faq.basics.bookieMoney.q'
  | 'support.faq.basics.bookieMoney.a'
  | 'support.faq.basics.overround.q'
  | 'support.faq.basics.overround.a'
  | 'support.faq.basics.live.q'
  | 'support.faq.basics.live.a'
  | 'support.faq.basics.cashout.q'
  | 'support.faq.basics.cashout.a'
  | 'support.faq.basics.handicap.q'
  | 'support.faq.basics.handicap.a'
  | 'support.faq.basics.asianHandicap.q'
  | 'support.faq.basics.asianHandicap.a'
  | 'support.faq.basics.ou25.q'
  | 'support.faq.basics.ou25.a'
  | 'support.faq.basics.btts.q'
  | 'support.faq.basics.btts.a'
  | 'support.faq.basics.dnb.q'
  | 'support.faq.basics.dnb.a'
  | 'support.faq.basics.doubleChance.q'
  | 'support.faq.basics.doubleChance.a'
  | 'support.faq.basics.specials.q'
  | 'support.faq.basics.specials.a'
  | 'support.faq.analysis.howTo.q'
  | 'support.faq.analysis.howTo.a'
  | 'support.faq.analysis.stats.q'
  | 'support.faq.analysis.stats.a'
  | 'support.faq.analysis.form.q'
  | 'support.faq.analysis.form.a'
  | 'support.faq.analysis.homeAway.q'
  | 'support.faq.analysis.homeAway.a'
  | 'support.faq.analysis.injuries.q'
  | 'support.faq.analysis.injuries.a'
  | 'support.faq.analysis.lineups.q'
  | 'support.faq.analysis.lineups.a'
  | 'support.faq.analysis.xg.q'
  | 'support.faq.analysis.xg.a'
  | 'support.faq.analysis.h2h.q'
  | 'support.faq.analysis.h2h.a'
  | 'support.faq.analysis.motivation.q'
  | 'support.faq.analysis.motivation.a'
  | 'support.faq.analysis.weather.q'
  | 'support.faq.analysis.weather.a'
  | 'support.faq.analysis.defOff.q'
  | 'support.faq.analysis.defOff.a'
  | 'support.faq.analysis.goalStats.q'
  | 'support.faq.analysis.goalStats.a'
  | 'support.faq.analysis.bestLeague.q'
  | 'support.faq.analysis.bestLeague.a'
  | 'support.faq.analysis.coach.q'
  | 'support.faq.analysis.coach.a'
  | 'support.faq.analysis.tempo.q'
  | 'support.faq.analysis.tempo.a'
  | 'support.faq.analysis.ouGames.q'
  | 'support.faq.analysis.ouGames.a'
  | 'support.faq.analysis.bttsGames.q'
  | 'support.faq.analysis.bttsGames.a'
  | 'support.faq.analysis.draws.q'
  | 'support.faq.analysis.draws.a'
  | 'support.faq.analysis.underdogs.q'
  | 'support.faq.analysis.underdogs.a'
  | 'support.faq.analysis.trapGames.q'
  | 'support.faq.analysis.trapGames.a'
  | 'support.faq.strategy.best.q'
  | 'support.faq.strategy.best.a'
  | 'support.faq.strategy.valueBet.q'
  | 'support.faq.strategy.valueBet.a'
  | 'support.faq.strategy.arbitrage.q'
  | 'support.faq.strategy.arbitrage.a'
  | 'support.faq.strategy.martingale.q'
  | 'support.faq.strategy.martingale.a'
  | 'support.faq.strategy.flat.q'
  | 'support.faq.strategy.flat.a'
  | 'support.faq.strategy.bankroll.q'
  | 'support.faq.strategy.bankroll.a'
  | 'support.faq.strategy.stake.q'
  | 'support.faq.strategy.stake.a'
  | 'support.faq.strategy.losingStreak.q'
  | 'support.faq.strategy.losingStreak.a'
  | 'support.faq.strategy.combos.q'
  | 'support.faq.strategy.combos.a'
  | 'support.faq.strategy.profitable.q'
  | 'support.faq.strategy.profitable.a'
  | 'support.faq.strategy.test.q'
  | 'support.faq.strategy.test.a'
  | 'support.faq.strategy.roi.q'
  | 'support.faq.strategy.roi.a'
  | 'support.faq.strategy.strikeRate.q'
  | 'support.faq.strategy.strikeRate.a'
  | 'support.faq.strategy.discipline.q'
  | 'support.faq.strategy.discipline.a'
  | 'support.faq.strategy.goodOdds.q'
  | 'support.faq.strategy.goodOdds.a'
  | 'support.faq.strategy.noBet.q'
  | 'support.faq.strategy.noBet.a'
  | 'support.faq.strategy.timing.q'
  | 'support.faq.strategy.timing.a'
  | 'support.faq.strategy.prematchLive.q'
  | 'support.faq.strategy.prematchLive.a'
  | 'support.faq.strategy.oddsMovement.q'
  | 'support.faq.strategy.oddsMovement.a'
  | 'support.faq.strategy.ownSystem.q'
  | 'support.faq.strategy.ownSystem.a'
  | 'support.faq.mistakes.loseMoney.q'
  | 'support.faq.mistakes.loseMoney.a'
  | 'support.faq.mistakes.chasing.q'
  | 'support.faq.mistakes.chasing.a'
  | 'support.faq.mistakes.emotions.q'
  | 'support.faq.mistakes.emotions.a'
  | 'support.faq.mistakes.accumulators.q'
  | 'support.faq.mistakes.accumulators.a'
  | 'support.faq.mistakes.overbetting.q'
  | 'support.faq.mistakes.overbetting.a'
  | 'support.faq.mistakes.tipsters.q'
  | 'support.faq.mistakes.tipsters.a'
  | 'support.faq.mistakes.noBankroll.q'
  | 'support.faq.mistakes.noBankroll.a'
  | 'support.faq.mistakes.sureBets.q'
  | 'support.faq.mistakes.sureBets.a'
  | 'support.faq.mistakes.favTeam.q'
  | 'support.faq.mistakes.favTeam.a'
  | 'support.faq.mistakes.beginner.q'
  | 'support.faq.mistakes.beginner.a'
  | 'support.faq.ai.how.q'
  | 'support.faq.ai.how.a'
  | 'support.faq.ai.data.q'
  | 'support.faq.ai.data.a'
  | 'support.faq.ai.reliability.q'
  | 'support.faq.ai.reliability.a'
  | 'support.faq.ai.model.q'
  | 'support.faq.ai.model.a'
  | 'support.faq.ai.ml.q'
  | 'support.faq.ai.ml.a'
  | 'support.faq.ai.features.q'
  | 'support.faq.ai.features.a'
  | 'support.faq.ai.history.q'
  | 'support.faq.ai.history.a'
  | 'support.faq.ai.oddsModel.q'
  | 'support.faq.ai.oddsModel.a'
  | 'support.faq.ai.valueBet.q'
  | 'support.faq.ai.valueBet.a'
  | 'support.faq.ai.overfitting.q'
  | 'support.faq.ai.overfitting.a'
  | 'support.faq.ai.algorithms.q'
  | 'support.faq.ai.algorithms.a'
  | 'support.faq.ai.liveData.q'
  | 'support.faq.ai.liveData.a'
  | 'support.faq.ai.realtime.q'
  | 'support.faq.ai.realtime.a'
  | 'support.faq.ai.measure.q'
  | 'support.faq.ai.measure.a'
  | 'support.faq.ai.improve.q'
  | 'support.faq.ai.improve.a'
  | 'support.faq.ai.combine.q'
  | 'support.faq.ai.combine.a'
  | 'support.faq.ai.ensemble.q'
  | 'support.faq.ai.ensemble.a'
  | 'support.faq.ai.apis.q'
  | 'support.faq.ai.apis.a'
  | 'support.faq.ai.dashboard.q'
  | 'support.faq.ai.dashboard.a'
  | 'support.faq.ai.automate.q'
  | 'support.faq.ai.automate.a'
  | 'support.faq.market.create.q'
  | 'support.faq.market.create.a'
  | 'support.faq.market.change.q'
  | 'support.faq.market.change.a'
  | 'support.faq.market.clv.q'
  | 'support.faq.market.clv.a'
  | 'support.faq.market.valueOdds.q'
  | 'support.faq.market.valueOdds.a'
  | 'support.faq.market.bestBooks.q'
  | 'support.faq.market.bestBooks.a'
  | 'support.faq.market.diffBooks.q'
  | 'support.faq.market.diffBooks.a'
  | 'support.faq.market.compare.q'
  | 'support.faq.market.compare.a'
  | 'support.faq.market.sharpPublic.q'
  | 'support.faq.market.sharpPublic.a'
  | 'support.faq.market.movement.q'
  | 'support.faq.market.movement.a'
  | 'support.faq.market.liquidity.q'
  | 'support.faq.market.liquidity.a'
  | 'support.faq.profit.earn.q'
  | 'support.faq.profit.earn.a'
  | 'support.faq.profit.longterm.q'
  | 'support.faq.profit.longterm.a'
  | 'support.faq.profit.roi.q'
  | 'support.faq.profit.roi.a'
  | 'support.faq.profit.timeToProfit.q'
  | 'support.faq.profit.timeToProfit.a'
  | 'support.faq.profit.capital.q'
  | 'support.faq.profit.capital.a'
  | 'support.faq.profit.skillVsLuck.q'
  | 'support.faq.profit.skillVsLuck.a'
  | 'support.faq.profit.prosVsAmateurs.q'
  | 'support.faq.profit.prosVsAmateurs.a'
  | 'support.faq.profit.prosWork.q'
  | 'support.faq.profit.prosWork.a'
  | 'support.faq.profit.patience.q'
  | 'support.faq.profit.patience.a'
  | 'support.faq.profit.fail90.q'
  | 'support.faq.profit.fail90.a'
  | 'support.faq.platform.daily.q'
  | 'support.faq.platform.daily.a'
  | 'support.faq.platform.autoload.q'
  | 'support.faq.platform.autoload.a'
  | 'support.faq.platform.updateFreq.q'
  | 'support.faq.platform.updateFreq.a'
  | 'support.faq.platform.confidence.q'
  | 'support.faq.platform.confidence.a'
  | 'support.faq.platform.visualize.q'
  | 'support.faq.platform.visualize.a'
  | 'support.faq.platform.bestBets.q'
  | 'support.faq.platform.bestBets.a'
  | 'support.faq.platform.history.q'
  | 'support.faq.platform.history.a'
  | 'support.faq.platform.tracking.q'
  | 'support.faq.platform.tracking.a'
  | 'support.faq.platform.ranking.q'
  | 'support.faq.platform.ranking.a'
  | 'support.faq.platform.lastBets.q'
  | 'support.faq.platform.lastBets.a'
  | 'support.faq.platform.wrongMatch.q'
  | 'support.faq.platform.wrongMatch.a'
  | 'support.faq.platform.valueVsPrediction.q'
  | 'support.faq.platform.valueVsPrediction.a'
  | 'support.faq.platform.alerts.q'
  | 'support.faq.platform.alerts.a'
  | 'support.faq.platform.trust.q'
  | 'support.faq.platform.trust.a'
  // <BEGIN_FOLLOWUP_KEYS>
  | 'support.faq.valueBet.fq'
  | 'support.faq.valueBet.fa'
  | 'support.faq.accuracy.fq'
  | 'support.faq.accuracy.fa'
  | 'support.faq.dataSource.fq'
  | 'support.faq.dataSource.fa'
  | 'support.faq.snapshotUpdate.fq'
  | 'support.faq.snapshotUpdate.fa'
  | 'support.faq.kelly.fq'
  | 'support.faq.kelly.fa'
  | 'support.faq.piRating.fq'
  | 'support.faq.piRating.fa'
  | 'support.faq.responsible.fq'
  | 'support.faq.responsible.fa'
  | 'support.faq.language.fq'
  | 'support.faq.language.fa'
  | 'support.faq.cookies.fq'
  | 'support.faq.cookies.fa'
  | 'support.faq.contact.fq'
  | 'support.faq.contact.fa'
  | 'support.faq.basics.oneX2.fq'
  | 'support.faq.basics.oneX2.fa'
  | 'support.faq.basics.odds.fq'
  | 'support.faq.basics.odds.fa'
  | 'support.faq.basics.winnings.fq'
  | 'support.faq.basics.winnings.fa'
  | 'support.faq.basics.single.fq'
  | 'support.faq.basics.single.fa'
  | 'support.faq.basics.accumulator.fq'
  | 'support.faq.basics.accumulator.fa'
  | 'support.faq.basics.system.fq'
  | 'support.faq.basics.system.fa'
  | 'support.faq.basics.valueBetBasic.fq'
  | 'support.faq.basics.valueBetBasic.fa'
  | 'support.faq.basics.probability.fq'
  | 'support.faq.basics.probability.fa'
  | 'support.faq.basics.bookie.fq'
  | 'support.faq.basics.bookie.fa'
  | 'support.faq.basics.bookieMoney.fq'
  | 'support.faq.basics.bookieMoney.fa'
  | 'support.faq.basics.overround.fq'
  | 'support.faq.basics.overround.fa'
  | 'support.faq.basics.live.fq'
  | 'support.faq.basics.live.fa'
  | 'support.faq.basics.cashout.fq'
  | 'support.faq.basics.cashout.fa'
  | 'support.faq.basics.handicap.fq'
  | 'support.faq.basics.handicap.fa'
  | 'support.faq.basics.asianHandicap.fq'
  | 'support.faq.basics.asianHandicap.fa'
  | 'support.faq.basics.ou25.fq'
  | 'support.faq.basics.ou25.fa'
  | 'support.faq.basics.btts.fq'
  | 'support.faq.basics.btts.fa'
  | 'support.faq.basics.dnb.fq'
  | 'support.faq.basics.dnb.fa'
  | 'support.faq.basics.doubleChance.fq'
  | 'support.faq.basics.doubleChance.fa'
  | 'support.faq.basics.specials.fq'
  | 'support.faq.basics.specials.fa'
  | 'support.faq.analysis.howTo.fq'
  | 'support.faq.analysis.howTo.fa'
  | 'support.faq.analysis.stats.fq'
  | 'support.faq.analysis.stats.fa'
  | 'support.faq.analysis.form.fq'
  | 'support.faq.analysis.form.fa'
  | 'support.faq.analysis.homeAway.fq'
  | 'support.faq.analysis.homeAway.fa'
  | 'support.faq.analysis.injuries.fq'
  | 'support.faq.analysis.injuries.fa'
  | 'support.faq.analysis.lineups.fq'
  | 'support.faq.analysis.lineups.fa'
  | 'support.faq.analysis.xg.fq'
  | 'support.faq.analysis.xg.fa'
  | 'support.faq.analysis.h2h.fq'
  | 'support.faq.analysis.h2h.fa'
  | 'support.faq.analysis.motivation.fq'
  | 'support.faq.analysis.motivation.fa'
  | 'support.faq.analysis.weather.fq'
  | 'support.faq.analysis.weather.fa'
  | 'support.faq.analysis.defOff.fq'
  | 'support.faq.analysis.defOff.fa'
  | 'support.faq.analysis.goalStats.fq'
  | 'support.faq.analysis.goalStats.fa'
  | 'support.faq.analysis.bestLeague.fq'
  | 'support.faq.analysis.bestLeague.fa'
  | 'support.faq.analysis.coach.fq'
  | 'support.faq.analysis.coach.fa'
  | 'support.faq.analysis.tempo.fq'
  | 'support.faq.analysis.tempo.fa'
  | 'support.faq.analysis.ouGames.fq'
  | 'support.faq.analysis.ouGames.fa'
  | 'support.faq.analysis.bttsGames.fq'
  | 'support.faq.analysis.bttsGames.fa'
  | 'support.faq.analysis.draws.fq'
  | 'support.faq.analysis.draws.fa'
  | 'support.faq.analysis.underdogs.fq'
  | 'support.faq.analysis.underdogs.fa'
  | 'support.faq.analysis.trapGames.fq'
  | 'support.faq.analysis.trapGames.fa'
  | 'support.faq.strategy.best.fq'
  | 'support.faq.strategy.best.fa'
  | 'support.faq.strategy.valueBet.fq'
  | 'support.faq.strategy.valueBet.fa'
  | 'support.faq.strategy.arbitrage.fq'
  | 'support.faq.strategy.arbitrage.fa'
  | 'support.faq.strategy.martingale.fq'
  | 'support.faq.strategy.martingale.fa'
  | 'support.faq.strategy.flat.fq'
  | 'support.faq.strategy.flat.fa'
  | 'support.faq.strategy.bankroll.fq'
  | 'support.faq.strategy.bankroll.fa'
  | 'support.faq.strategy.stake.fq'
  | 'support.faq.strategy.stake.fa'
  | 'support.faq.strategy.losingStreak.fq'
  | 'support.faq.strategy.losingStreak.fa'
  | 'support.faq.strategy.combos.fq'
  | 'support.faq.strategy.combos.fa'
  | 'support.faq.strategy.profitable.fq'
  | 'support.faq.strategy.profitable.fa'
  | 'support.faq.strategy.test.fq'
  | 'support.faq.strategy.test.fa'
  | 'support.faq.strategy.roi.fq'
  | 'support.faq.strategy.roi.fa'
  | 'support.faq.strategy.strikeRate.fq'
  | 'support.faq.strategy.strikeRate.fa'
  | 'support.faq.strategy.discipline.fq'
  | 'support.faq.strategy.discipline.fa'
  | 'support.faq.strategy.goodOdds.fq'
  | 'support.faq.strategy.goodOdds.fa'
  | 'support.faq.strategy.noBet.fq'
  | 'support.faq.strategy.noBet.fa'
  | 'support.faq.strategy.timing.fq'
  | 'support.faq.strategy.timing.fa'
  | 'support.faq.strategy.prematchLive.fq'
  | 'support.faq.strategy.prematchLive.fa'
  | 'support.faq.strategy.oddsMovement.fq'
  | 'support.faq.strategy.oddsMovement.fa'
  | 'support.faq.strategy.ownSystem.fq'
  | 'support.faq.strategy.ownSystem.fa'
  | 'support.faq.mistakes.loseMoney.fq'
  | 'support.faq.mistakes.loseMoney.fa'
  | 'support.faq.mistakes.chasing.fq'
  | 'support.faq.mistakes.chasing.fa'
  | 'support.faq.mistakes.emotions.fq'
  | 'support.faq.mistakes.emotions.fa'
  | 'support.faq.mistakes.accumulators.fq'
  | 'support.faq.mistakes.accumulators.fa'
  | 'support.faq.mistakes.overbetting.fq'
  | 'support.faq.mistakes.overbetting.fa'
  | 'support.faq.mistakes.tipsters.fq'
  | 'support.faq.mistakes.tipsters.fa'
  | 'support.faq.mistakes.noBankroll.fq'
  | 'support.faq.mistakes.noBankroll.fa'
  | 'support.faq.mistakes.sureBets.fq'
  | 'support.faq.mistakes.sureBets.fa'
  | 'support.faq.mistakes.favTeam.fq'
  | 'support.faq.mistakes.favTeam.fa'
  | 'support.faq.mistakes.beginner.fq'
  | 'support.faq.mistakes.beginner.fa'
  | 'support.faq.ai.how.fq'
  | 'support.faq.ai.how.fa'
  | 'support.faq.ai.data.fq'
  | 'support.faq.ai.data.fa'
  | 'support.faq.ai.reliability.fq'
  | 'support.faq.ai.reliability.fa'
  | 'support.faq.ai.model.fq'
  | 'support.faq.ai.model.fa'
  | 'support.faq.ai.ml.fq'
  | 'support.faq.ai.ml.fa'
  | 'support.faq.ai.features.fq'
  | 'support.faq.ai.features.fa'
  | 'support.faq.ai.history.fq'
  | 'support.faq.ai.history.fa'
  | 'support.faq.ai.oddsModel.fq'
  | 'support.faq.ai.oddsModel.fa'
  | 'support.faq.ai.valueBet.fq'
  | 'support.faq.ai.valueBet.fa'
  | 'support.faq.ai.overfitting.fq'
  | 'support.faq.ai.overfitting.fa'
  | 'support.faq.ai.algorithms.fq'
  | 'support.faq.ai.algorithms.fa'
  | 'support.faq.ai.liveData.fq'
  | 'support.faq.ai.liveData.fa'
  | 'support.faq.ai.realtime.fq'
  | 'support.faq.ai.realtime.fa'
  | 'support.faq.ai.measure.fq'
  | 'support.faq.ai.measure.fa'
  | 'support.faq.ai.improve.fq'
  | 'support.faq.ai.improve.fa'
  | 'support.faq.ai.combine.fq'
  | 'support.faq.ai.combine.fa'
  | 'support.faq.ai.ensemble.fq'
  | 'support.faq.ai.ensemble.fa'
  | 'support.faq.ai.apis.fq'
  | 'support.faq.ai.apis.fa'
  | 'support.faq.ai.dashboard.fq'
  | 'support.faq.ai.dashboard.fa'
  | 'support.faq.ai.automate.fq'
  | 'support.faq.ai.automate.fa'
  | 'support.faq.market.create.fq'
  | 'support.faq.market.create.fa'
  | 'support.faq.market.change.fq'
  | 'support.faq.market.change.fa'
  | 'support.faq.market.clv.fq'
  | 'support.faq.market.clv.fa'
  | 'support.faq.market.valueOdds.fq'
  | 'support.faq.market.valueOdds.fa'
  | 'support.faq.market.bestBooks.fq'
  | 'support.faq.market.bestBooks.fa'
  | 'support.faq.market.diffBooks.fq'
  | 'support.faq.market.diffBooks.fa'
  | 'support.faq.market.compare.fq'
  | 'support.faq.market.compare.fa'
  | 'support.faq.market.sharpPublic.fq'
  | 'support.faq.market.sharpPublic.fa'
  | 'support.faq.market.movement.fq'
  | 'support.faq.market.movement.fa'
  | 'support.faq.market.liquidity.fq'
  | 'support.faq.market.liquidity.fa'
  | 'support.faq.profit.earn.fq'
  | 'support.faq.profit.earn.fa'
  | 'support.faq.profit.longterm.fq'
  | 'support.faq.profit.longterm.fa'
  | 'support.faq.profit.roi.fq'
  | 'support.faq.profit.roi.fa'
  | 'support.faq.profit.timeToProfit.fq'
  | 'support.faq.profit.timeToProfit.fa'
  | 'support.faq.profit.capital.fq'
  | 'support.faq.profit.capital.fa'
  | 'support.faq.profit.skillVsLuck.fq'
  | 'support.faq.profit.skillVsLuck.fa'
  | 'support.faq.profit.prosVsAmateurs.fq'
  | 'support.faq.profit.prosVsAmateurs.fa'
  | 'support.faq.profit.prosWork.fq'
  | 'support.faq.profit.prosWork.fa'
  | 'support.faq.profit.patience.fq'
  | 'support.faq.profit.patience.fa'
  | 'support.faq.profit.fail90.fq'
  | 'support.faq.profit.fail90.fa'
  | 'support.faq.platform.daily.fq'
  | 'support.faq.platform.daily.fa'
  | 'support.faq.platform.autoload.fq'
  | 'support.faq.platform.autoload.fa'
  | 'support.faq.platform.updateFreq.fq'
  | 'support.faq.platform.updateFreq.fa'
  | 'support.faq.platform.confidence.fq'
  | 'support.faq.platform.confidence.fa'
  | 'support.faq.platform.visualize.fq'
  | 'support.faq.platform.visualize.fa'
  | 'support.faq.platform.bestBets.fq'
  | 'support.faq.platform.bestBets.fa'
  | 'support.faq.platform.history.fq'
  | 'support.faq.platform.history.fa'
  | 'support.faq.platform.tracking.fq'
  | 'support.faq.platform.tracking.fa'
  | 'support.faq.platform.ranking.fq'
  | 'support.faq.platform.ranking.fa'
  | 'support.faq.platform.lastBets.fq'
  | 'support.faq.platform.lastBets.fa'
  | 'support.faq.platform.wrongMatch.fq'
  | 'support.faq.platform.wrongMatch.fa'
  | 'support.faq.platform.valueVsPrediction.fq'
  | 'support.faq.platform.valueVsPrediction.fa'
  | 'support.faq.platform.alerts.fq'
  | 'support.faq.platform.alerts.fa'
  | 'support.faq.platform.trust.fq'
  | 'support.faq.platform.trust.fa'
  | 'support.faq.valueBet.alt1'
  | 'support.faq.valueBet.alt2'
  | 'support.faq.valueBet.alt3'
  | 'support.faq.valueBet.alt4'
  | 'support.faq.valueBet.alt5'
  | 'support.faq.accuracy.alt1'
  | 'support.faq.accuracy.alt2'
  | 'support.faq.accuracy.alt3'
  | 'support.faq.accuracy.alt4'
  | 'support.faq.accuracy.alt5'
  | 'support.faq.dataSource.alt1'
  | 'support.faq.dataSource.alt2'
  | 'support.faq.dataSource.alt3'
  | 'support.faq.dataSource.alt4'
  | 'support.faq.dataSource.alt5'
  | 'support.faq.snapshotUpdate.alt1'
  | 'support.faq.snapshotUpdate.alt2'
  | 'support.faq.snapshotUpdate.alt3'
  | 'support.faq.snapshotUpdate.alt4'
  | 'support.faq.snapshotUpdate.alt5'
  | 'support.faq.kelly.alt1'
  | 'support.faq.kelly.alt2'
  | 'support.faq.kelly.alt3'
  | 'support.faq.kelly.alt4'
  | 'support.faq.kelly.alt5'
  | 'support.faq.piRating.alt1'
  | 'support.faq.piRating.alt2'
  | 'support.faq.piRating.alt3'
  | 'support.faq.piRating.alt4'
  | 'support.faq.piRating.alt5'
  | 'support.faq.responsible.alt1'
  | 'support.faq.responsible.alt2'
  | 'support.faq.responsible.alt3'
  | 'support.faq.responsible.alt4'
  | 'support.faq.responsible.alt5'
  | 'support.faq.language.alt1'
  | 'support.faq.language.alt2'
  | 'support.faq.language.alt3'
  | 'support.faq.language.alt4'
  | 'support.faq.language.alt5'
  | 'support.faq.cookies.alt1'
  | 'support.faq.cookies.alt2'
  | 'support.faq.cookies.alt3'
  | 'support.faq.cookies.alt4'
  | 'support.faq.cookies.alt5'
  | 'support.faq.contact.alt1'
  | 'support.faq.contact.alt2'
  | 'support.faq.contact.alt3'
  | 'support.faq.contact.alt4'
  | 'support.faq.contact.alt5'
  | 'support.faq.basics.oneX2.alt1'
  | 'support.faq.basics.oneX2.alt2'
  | 'support.faq.basics.oneX2.alt3'
  | 'support.faq.basics.oneX2.alt4'
  | 'support.faq.basics.oneX2.alt5'
  | 'support.faq.basics.odds.alt1'
  | 'support.faq.basics.odds.alt2'
  | 'support.faq.basics.odds.alt3'
  | 'support.faq.basics.odds.alt4'
  | 'support.faq.basics.odds.alt5'
  | 'support.faq.basics.winnings.alt1'
  | 'support.faq.basics.winnings.alt2'
  | 'support.faq.basics.winnings.alt3'
  | 'support.faq.basics.winnings.alt4'
  | 'support.faq.basics.winnings.alt5'
  | 'support.faq.basics.single.alt1'
  | 'support.faq.basics.single.alt2'
  | 'support.faq.basics.single.alt3'
  | 'support.faq.basics.single.alt4'
  | 'support.faq.basics.single.alt5'
  | 'support.faq.basics.accumulator.alt1'
  | 'support.faq.basics.accumulator.alt2'
  | 'support.faq.basics.accumulator.alt3'
  | 'support.faq.basics.accumulator.alt4'
  | 'support.faq.basics.accumulator.alt5'
  | 'support.faq.basics.system.alt1'
  | 'support.faq.basics.system.alt2'
  | 'support.faq.basics.system.alt3'
  | 'support.faq.basics.system.alt4'
  | 'support.faq.basics.system.alt5'
  | 'support.faq.basics.valueBetBasic.alt1'
  | 'support.faq.basics.valueBetBasic.alt2'
  | 'support.faq.basics.valueBetBasic.alt3'
  | 'support.faq.basics.valueBetBasic.alt4'
  | 'support.faq.basics.valueBetBasic.alt5'
  | 'support.faq.basics.probability.alt1'
  | 'support.faq.basics.probability.alt2'
  | 'support.faq.basics.probability.alt3'
  | 'support.faq.basics.probability.alt4'
  | 'support.faq.basics.probability.alt5'
  | 'support.faq.basics.bookie.alt1'
  | 'support.faq.basics.bookie.alt2'
  | 'support.faq.basics.bookie.alt3'
  | 'support.faq.basics.bookie.alt4'
  | 'support.faq.basics.bookie.alt5'
  | 'support.faq.basics.bookieMoney.alt1'
  | 'support.faq.basics.bookieMoney.alt2'
  | 'support.faq.basics.bookieMoney.alt3'
  | 'support.faq.basics.bookieMoney.alt4'
  | 'support.faq.basics.bookieMoney.alt5'
  | 'support.faq.basics.overround.alt1'
  | 'support.faq.basics.overround.alt2'
  | 'support.faq.basics.overround.alt3'
  | 'support.faq.basics.overround.alt4'
  | 'support.faq.basics.overround.alt5'
  | 'support.faq.basics.live.alt1'
  | 'support.faq.basics.live.alt2'
  | 'support.faq.basics.live.alt3'
  | 'support.faq.basics.live.alt4'
  | 'support.faq.basics.live.alt5'
  | 'support.faq.basics.cashout.alt1'
  | 'support.faq.basics.cashout.alt2'
  | 'support.faq.basics.cashout.alt3'
  | 'support.faq.basics.cashout.alt4'
  | 'support.faq.basics.cashout.alt5'
  | 'support.faq.basics.handicap.alt1'
  | 'support.faq.basics.handicap.alt2'
  | 'support.faq.basics.handicap.alt3'
  | 'support.faq.basics.handicap.alt4'
  | 'support.faq.basics.handicap.alt5'
  | 'support.faq.basics.asianHandicap.alt1'
  | 'support.faq.basics.asianHandicap.alt2'
  | 'support.faq.basics.asianHandicap.alt3'
  | 'support.faq.basics.asianHandicap.alt4'
  | 'support.faq.basics.asianHandicap.alt5'
  | 'support.faq.basics.ou25.alt1'
  | 'support.faq.basics.ou25.alt2'
  | 'support.faq.basics.ou25.alt3'
  | 'support.faq.basics.ou25.alt4'
  | 'support.faq.basics.ou25.alt5'
  | 'support.faq.basics.btts.alt1'
  | 'support.faq.basics.btts.alt2'
  | 'support.faq.basics.btts.alt3'
  | 'support.faq.basics.btts.alt4'
  | 'support.faq.basics.btts.alt5'
  | 'support.faq.basics.dnb.alt1'
  | 'support.faq.basics.dnb.alt2'
  | 'support.faq.basics.dnb.alt3'
  | 'support.faq.basics.dnb.alt4'
  | 'support.faq.basics.dnb.alt5'
  | 'support.faq.basics.doubleChance.alt1'
  | 'support.faq.basics.doubleChance.alt2'
  | 'support.faq.basics.doubleChance.alt3'
  | 'support.faq.basics.doubleChance.alt4'
  | 'support.faq.basics.doubleChance.alt5'
  | 'support.faq.basics.specials.alt1'
  | 'support.faq.basics.specials.alt2'
  | 'support.faq.basics.specials.alt3'
  | 'support.faq.basics.specials.alt4'
  | 'support.faq.basics.specials.alt5'
  // <END_FOLLOWUP_KEYS>;
export const en: Dictionary = {
  'site.title': 'Betting with AI',
  'site.tagline':
    "Today's AI-driven betting analyses for the Top 5 football leagues.",
  'site.description':
    'Data-driven football predictions and value bets for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship. Powered by NOMEN — our hybrid machine-learning model for predicting match outcomes, goals and betting value, with transparent performance tracking.',
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
  'transparency.group.valueBets': 'Value Bets',
  'transparency.group.predictions': '1x2 Predictions',
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
  'predictionCard.stake': 'Stake:',
  'predictionCard.noStake': 'No stake (confidence too low)',
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
  'bankroll.series.valueBets': 'Value Bets',
  'bankroll.series.predictions': '1x2 Predictions',
  'bankroll.series.combined': 'Combined',
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
  'breadcrumb.home': 'Home',
  'rail.section.explore': 'Explore',
  'rail.section.spaces': 'Leagues',
  'rail.section.today': 'Today',
  'rail.spaces.all': 'All leagues',
  'rail.today.empty': 'No upcoming kickoffs.',
  'rail.today.snapshot': 'Predictions · updated {age} ago',
  'rail.quick.learn': 'Learn',
  'rail.quick.trackRecord': 'Track record',
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
  'support.toggle.label': 'Help / Support',
  'support.panel.title': 'Support chat',
  'support.panel.close': 'Close support chat',
  'support.input.placeholder': 'Ask a question…',
  'support.input.send': 'Send',
  'support.suggestions.heading': 'Common questions',
  'support.reset': 'Back to questions',
  'support.fallback':
    "Sorry, I couldn't find an exact answer. Try rephrasing, or reach out via the contact details in the footer.",
  'support.faq.valueBet.q': 'What is a value bet?',
  'support.faq.valueBet.a':
    'A value bet is a wager where our model estimates the true win probability to be higher than implied by the bookmaker odds. The resulting edge is what makes the bet +EV in the long run.',
  'support.faq.accuracy.q': 'How accurate are the predictions?',
  'support.faq.accuracy.a':
    'We use an ensemble of CatBoost + Dixon-Coles Poisson + an MLP, calibrated with isotonic regression. Typical RPS lies between 0.18 and 0.21 per league. See the Track Record page for a verified log.',
  'support.faq.dataSource.q': 'Where does the data come from?',
  'support.faq.dataSource.a':
    'Match results and closing odds come from Football-Data.co.uk CSV feeds for the Top 5 leagues. Optional lineup and xG data is pulled from Sofascore (opt-in only).',
  'support.faq.snapshotUpdate.q': 'How often are predictions updated?',
  'support.faq.snapshotUpdate.a':
    'A fresh snapshot is generated every morning. During live matchdays the value-bet list refreshes every 45–60 seconds as odds move.',
  'support.faq.kelly.q': 'How is the recommended stake calculated?',
  'support.faq.kelly.a':
    'We apply a fractional Kelly criterion (¼ Kelly) capped at 5% of bankroll per bet: f* = (p · o − 1) / (o − 1), where p is our calibrated probability and o the decimal odds. This reduces variance vs full Kelly.',
  'support.faq.piRating.q': 'What is a Pi-Rating?',
  'support.faq.piRating.a':
    'Pi-Ratings (Constantinou & Fenton, 2013) split each team into a home and away strength and update after every match by the residual between predicted and actual goal difference. They feed directly into our Poisson model.',
  'support.faq.responsible.q': 'Is this financial or betting advice?',
  'support.faq.responsible.a':
    "No. Betting with AI is informational only and not a solicitation to gamble. We never accept stakes. Please gamble responsibly — see the Responsible Gambling page for helplines and self-exclusion tools.",
  'support.faq.language.q': 'How do I change the language?',
  'support.faq.language.a':
    'Use the language switcher in the top navigation bar. We currently support English, German, Spanish, French and Italian.',
  'support.faq.cookies.q': 'How do I change my cookie preferences?',
  'support.faq.cookies.a':
    "Open the footer and click 'Cookies' — you can re-open the consent dialog there and adjust analytics or marketing cookies at any time.",
  'support.faq.contact.q': 'How can I contact the team?',
  'support.faq.contact.a':
    'Contact details are in the Impressum (footer). For technical issues, please open an issue on the public source-code repository linked in the footer.',
  'support.faq.basics.oneX2.q': "What does 1X2 mean in football betting?",
  'support.faq.basics.oneX2.a': "1X2 is the classic three-way market: 1 = home win, X = draw, 2 = away win.",
  'support.faq.basics.odds.q': "What are odds and how do they work?",
  'support.faq.basics.odds.a': "Decimal odds express the total payout factor: stake × odds = gross return. The reciprocal 1/odds is the market-implied probability.",
  'support.faq.basics.winnings.q': "How do I calculate the winnings on a bet?",
  'support.faq.basics.winnings.a': "Net profit = stake × (odds − 1). Example: €10 at 2.50 → €15 net profit, €25 total payout.",
  'support.faq.basics.single.q': "What is a single bet?",
  'support.faq.basics.single.a': "A single bet places a stake on exactly one event. It wins only if that one selection is correct.",
  'support.faq.basics.accumulator.q': "What is an accumulator (combo bet)?",
  'support.faq.basics.accumulator.a': "An accumulator combines multiple picks; odds multiply. It only wins if every selection wins.",
  'support.faq.basics.system.q': "What is a system bet?",
  'support.faq.basics.system.a': "A system bet covers all sub-combinations out of N picks (e.g. 2-from-3). Some selections may lose and the bet still pays out partially.",
  'support.faq.basics.valueBetBasic.q': "What does \"value bet\" mean?",
  'support.faq.basics.valueBetBasic.a': "A value bet exists when the true probability of an outcome exceeds the probability implied by the odds (p × odds > 1). It is +EV in the long run.",
  'support.faq.basics.probability.q': "What is the probability implied by odds?",
  'support.faq.basics.probability.a': "The implied probability of a decimal odd is 1/odds. Example: 2.00 → 50%, 4.00 → 25%. The three 1X2 probabilities sum above 100% because of the margin.",
  'support.faq.basics.bookie.q': "What is a bookmaker (bookie)?",
  'support.faq.basics.bookie.a': "A bookmaker is the operator that sets odds, accepts stakes and pays out winnings.",
  'support.faq.basics.bookieMoney.q': "How do bookmakers make money?",
  'support.faq.basics.bookieMoney.a': "Via the overround: implied probabilities of a market sum above 100%, and that excess is the bookie's statistical profit.",
  'support.faq.basics.overround.q': "What is the overround (margin)?",
  'support.faq.basics.overround.a': "Overround = Σ(1/odds) − 1. A value of e.g. 5% represents the bookmaker margin baked into the market.",
  'support.faq.basics.live.q': "What is a live (in-play) bet?",
  'support.faq.basics.live.a': "Live bets are placed during the match. Odds update minute by minute based on in-game events such as goals or red cards.",
  'support.faq.basics.cashout.q': "What is cash-out?",
  'support.faq.basics.cashout.a': "Cash-out lets you settle an open bet early at a price the bookmaker currently offers. The operator usually takes an extra margin for it.",
  'support.faq.basics.handicap.q': "What is a handicap bet?",
  'support.faq.basics.handicap.a': "In a handicap bet one team starts with a virtual goal advantage or disadvantage (e.g. −1) that adjusts the result for settlement.",
  'support.faq.basics.asianHandicap.q': "What is an Asian handicap?",
  'support.faq.basics.asianHandicap.a': "The Asian handicap removes the draw and uses quarter or half lines (e.g. −0.25, −0.75), sometimes refunding half the stake.",
  'support.faq.basics.ou25.q': "What is Over/Under 2.5 goals?",
  'support.faq.basics.ou25.a': "Over 2.5 wins with 3 or more total goals, Under 2.5 with 2 or fewer. Exactly 2 goals counts as Under.",
  'support.faq.basics.btts.q': "What does BTTS (Both Teams To Score) mean?",
  'support.faq.basics.btts.a': "BTTS \"Yes\" wins if both teams score at least one goal, regardless of the final result.",
  'support.faq.basics.dnb.q': "What is Draw No Bet?",
  'support.faq.basics.dnb.a': "Draw No Bet backs a home or away win; if the match ends in a draw, your stake is refunded.",
  'support.faq.basics.doubleChance.q': "What is Double Chance?",
  'support.faq.basics.doubleChance.a': "Double Chance covers two of the three 1X2 outcomes (1X, X2, 12). Higher hit rate, much lower odds.",
  'support.faq.basics.specials.q': "What are special bets (e.g. goalscorer)?",
  'support.faq.basics.specials.a': "Specials target events beyond the final result: goalscorer, cards, corners, half-time score, player goal count.",
  'support.faq.analysis.howTo.q': "How do I analyse a football match correctly?",
  'support.faq.analysis.howTo.a': "Combine form, home/away strength, xG trends, injuries, H2H and motivation. Cross-check these cues against our calibrated model probabilities.",
  'support.faq.analysis.stats.q': "Which statistics matter most?",
  'support.faq.analysis.stats.a': "xG and xGA, shots on target, possession in the opposition half, PPDA and expected points (xPts) carry the most predictive signal.",
  'support.faq.analysis.form.q': "How important is current team form?",
  'support.faq.analysis.form.a': "Form provides a short-term signal but can mislead as it ignores opposition quality. Strength-adjusted xG is far more informative than raw points runs.",
  'support.faq.analysis.homeAway.q': "How important is home vs away?",
  'support.faq.analysis.homeAway.a': "Home advantage is roughly +0.3 goals across European leagues. Pi-Ratings split home/away strength explicitly and capture this effect cleanly.",
  'support.faq.analysis.injuries.q': "How do injuries affect the forecast?",
  'support.faq.analysis.injuries.a': "Key absences (keeper, top striker, defensive spine) can shift win probability by 5–10 pp. We re-check lineups ~1h before kickoff.",
  'support.faq.analysis.lineups.q': "How important are lineups?",
  'support.faq.analysis.lineups.a': "Official lineups (usually T−60 min) are one of the strongest short-horizon features. Our pipeline ingests them optionally via Sofascore.",
  'support.faq.analysis.xg.q': "What role does xG (Expected Goals) play?",
  'support.faq.analysis.xg.a': "xG measures chance quality instead of noisy finishing. Over 10–15 matches xG is a far better forecast driver than raw goal tallies.",
  'support.faq.analysis.h2h.q': "How do I analyse head-to-head data?",
  'support.faq.analysis.h2h.a': "H2H has low predictive power when squads and coaches rotate. Only use matches with the same managers/core squad and weight them lightly.",
  'support.faq.analysis.motivation.q': "How much does motivation (e.g. relegation battle) matter?",
  'support.faq.analysis.motivation.a': "League position shapes risk appetite and rotation. A motivation feature (relegation/title/Europe pressure) measurably improves end-of-season RPS.",
  'support.faq.analysis.weather.q': "How does weather influence a match?",
  'support.faq.analysis.weather.a': "Strong wind and heavy rain reduce goal probability (Under bias). In top leagues the effect is small (~0.1–0.2 goals) but notable at extremes.",
  'support.faq.analysis.defOff.q': "How do I spot defensive vs offensive teams?",
  'support.faq.analysis.defOff.a': "Compare xG differential, shots per game and PPDA. High pressing + high possession = attacking; low PPDA and deep block = defensive.",
  'support.faq.analysis.goalStats.q': "How do I analyse goal statistics?",
  'support.faq.analysis.goalStats.a': "Split goals for and goals against per 90 minutes, home/away separately, and normalise for opposition. Combine with xG/xGA to separate luck from skill.",
  'support.faq.analysis.bestLeague.q': "Which league is most predictable?",
  'support.faq.analysis.bestLeague.a': "Top-5 leagues with rich data and stable squads forecast best. In our backtests the Premier League and La Liga post the lowest RPS.",
  'support.faq.analysis.coach.q': "How important are managerial changes?",
  'support.faq.analysis.coach.a': "A managerial change creates a measurable bounce-back effect over 3–6 matches. Our model down-weights historical form within this window.",
  'support.faq.analysis.tempo.q': "How do I analyse tempo and tactics?",
  'support.faq.analysis.tempo.a': "High pressing + vertical play creates more xG events per minute. Use PPDA, passes per defensive action and defensive-line height as proxies.",
  'support.faq.analysis.ouGames.q': "How do I spot Over/Under matches?",
  'support.faq.analysis.ouGames.a': "Sum both teams' offensive xG with their defensive xGA to estimate total expected goals. > 2.8 suggests Over, < 2.2 suggests Under.",
  'support.faq.analysis.bttsGames.q': "How do I identify BTTS matches?",
  'support.faq.analysis.bttsGames.a': "Both sides should have > 70% BTTS rate in the last 8 matches, both post xG > 1.0 and neither have a top defence.",
  'support.faq.analysis.draws.q': "Which factors drive draws?",
  'support.faq.analysis.draws.a': "Draws become likelier with similar team strengths, low total expected goals and defensive setups (deep block).",
  'support.faq.analysis.underdogs.q': "How do I analyse underdogs?",
  'support.faq.analysis.underdogs.a': "High market margin tends to push underdog odds too high. Check xG differential, home advantage and motivation — value often sits on the 1X or X2 side.",
  'support.faq.analysis.trapGames.q': "How do I recognise \"trap games\"?",
  'support.faq.analysis.trapGames.a': "Watch for rotation before cup/European fixtures, overrated favourites after winning streaks and derbies with emotional upside risk.",
  'support.faq.strategy.best.q': "What is the best football betting strategy?",
  'support.faq.strategy.best.a': "No strategy is universally \"best\". Winning approaches combine data-driven value betting, strict bankroll management and a documented rule for every bet.",
  'support.faq.strategy.valueBet.q': "What is value betting exactly?",
  'support.faq.strategy.valueBet.a': "Value betting only places bets where model probability × odds > 1. The edge (model − market) is the expected profit per unit staked.",
  'support.faq.strategy.arbitrage.q': "What is arbitrage betting?",
  'support.faq.strategy.arbitrage.a': "Arbitrage exploits odds gaps across bookmakers so every outcome is covered for a small guaranteed profit. It works but gets limited by operators quickly.",
  'support.faq.strategy.martingale.q': "What is Martingale (and why dangerous)?",
  'support.faq.strategy.martingale.a': "Martingale doubles stake after every loss. A short losing streak wipes out the bankroll or hits table limits — negative EV in the long run.",
  'support.faq.strategy.flat.q': "What is flat betting?",
  'support.faq.strategy.flat.a': "Flat betting uses the same stake (e.g. 1–2% of bankroll) on every bet — robust, low variance, ideal to measure your true edge.",
  'support.faq.strategy.bankroll.q': "How does bankroll management work?",
  'support.faq.strategy.bankroll.a': "Ring-fence a dedicated betting budget and stake 1–2% per bet (or fractional Kelly with a cap). Goal: survive drawdowns without abandoning the strategy.",
  'support.faq.strategy.stake.q': "How much should I stake per bet?",
  'support.faq.strategy.stake.a': "Rule of thumb: 1% flat, or f* = ¼ × Kelly capped at 5%. If confidence in the edge is low, drop to 0.5%.",
  'support.faq.strategy.losingStreak.q': "How do I avoid losing streaks?",
  'support.faq.strategy.losingStreak.a': "Losing streaks are unavoidable; what matters is shrinking stake size (Kelly does this naturally) and not rewriting the strategy out of frustration.",
  'support.faq.strategy.combos.q': "Should I play accumulators?",
  'support.faq.strategy.combos.a': "Accumulators multiply the bookmaker margin too. From a +EV standpoint they only pay off if every leg has strong standalone value — rare in practice.",
  'support.faq.strategy.profitable.q': "How do I find long-term profitable strategies?",
  'support.faq.strategy.profitable.a': "Systematic: explicit rule, backtest over ≥ 1,000 bets, positive CLV, positive ROI net of margin, strict risk control.",
  'support.faq.strategy.test.q': "How do I test a strategy?",
  'support.faq.strategy.test.a': "Walk-forward backtest on historical closing odds: define a training window, evaluate rolling out-of-sample and track RPS, Brier, ROI and CLV.",
  'support.faq.strategy.roi.q': "What is ROI in betting?",
  'support.faq.strategy.roi.a': "ROI = (net profit / total stake) × 100%. 2–5% is realistic long-term; anything > 10% sustained over many bets is exceptionally rare and suspect.",
  'support.faq.strategy.strikeRate.q': "What is strike rate?",
  'support.faq.strategy.strikeRate.a': "Strike rate = wins / bets placed. Meaningless on its own — only informative combined with average odds and ROI.",
  'support.faq.strategy.discipline.q': "How important is discipline?",
  'support.faq.strategy.discipline.a': "Discipline is the single biggest driver. Stick to the rules, skip impulse bets, never chase losses with bigger stakes.",
  'support.faq.strategy.goodOdds.q': "How do I spot good vs bad odds?",
  'support.faq.strategy.goodOdds.a': "Good odds exceed the model's fair price (1/probability) and sit near the closing line. Use an odds comparator and your own fair value.",
  'support.faq.strategy.noBet.q': "When should I not bet?",
  'support.faq.strategy.noBet.a': "No edge, fuzzy data, emotional ties to the team or fatigue — in all those cases \"no bet\" is the most profitable call.",
  'support.faq.strategy.timing.q': "How important is timing?",
  'support.faq.strategy.timing.a': "Early odds often carry more value; late odds are sharper (CLV benchmark). Sharps bet early to lock in positive CLV.",
  'support.faq.strategy.prematchLive.q': "Pre-match vs live — which is better?",
  'support.faq.strategy.prematchLive.a': "Pre-match: lower margin and more analysis time. Live: more market inefficiencies around quick events but higher margin and stronger emotions.",
  'support.faq.strategy.oddsMovement.q': "How do I use odds movement?",
  'support.faq.strategy.oddsMovement.a': "A clean drop toward an outcome signals sharp money. Take value bets early before the line moves, then use CLV as a quality check.",
  'support.faq.strategy.ownSystem.q': "How do I build my own betting system?",
  'support.faq.strategy.ownSystem.a': "Define features → train a model (logistic or CatBoost) → calibrate → walk-forward backtest → track live ROI & CLV → iterate.",
  'support.faq.mistakes.loseMoney.q': "Why do most bettors lose money?",
  'support.faq.mistakes.loseMoney.a': "Bookmaker margin, no model, emotional picks and no bankroll plan. Without a measurable edge betting is mathematically a loss.",
  'support.faq.mistakes.chasing.q': "What does \"chasing losses\" mean?",
  'support.faq.mistakes.chasing.a': "Chasing = raising stakes after losses to \"win it back\". Mathematically produces exponentially bigger losses — never do it.",
  'support.faq.mistakes.emotions.q': "Why are emotions dangerous in betting?",
  'support.faq.mistakes.emotions.a': "Tilt causes over-staking, chasing and rule-breaking. A fixed plan plus a break after 3 losses is the best defence.",
  'support.faq.mistakes.accumulators.q': "Why are accumulators risky?",
  'support.faq.mistakes.accumulators.a': "5 picks at 55% each give a combined probability below 6%. Multiplied margin also eats up the expected profit.",
  'support.faq.mistakes.overbetting.q': "Why is overbetting bad?",
  'support.faq.mistakes.overbetting.a': "Overbetting exceeds Kelly-optimal stake and raises ruin risk exponentially — even a +EV edge can wipe the bankroll.",
  'support.faq.mistakes.tipsters.q': "Why not blindly follow tipsters?",
  'support.faq.mistakes.tipsters.a': "Public tipsters rarely have verified track records and earn from subscriptions, not edge. Own analysis or calibrated models beat them.",
  'support.faq.mistakes.noBankroll.q': "Why is a lack of bankroll management fatal?",
  'support.faq.mistakes.noBankroll.a': "Without a plan you stake on feel — a normal losing run of 10 can wipe out the entire bankroll.",
  'support.faq.mistakes.sureBets.q': "Why are \"sure tips\" dangerous?",
  'support.faq.mistakes.sureBets.a': "No bet is ever safe — even 1.05 odds lose sometimes. \"Sure tips\" are usually marketing and push users to over-stake.",
  'support.faq.mistakes.favTeam.q': "Why shouldn't you bet on your favourite club?",
  'support.faq.mistakes.favTeam.a': "Confirmation bias systematically overrates your own club's strength. Result: negative EV and emotional in-game decisions.",
  'support.faq.mistakes.beginner.q': "How do I avoid beginner mistakes?",
  'support.faq.mistakes.beginner.a': "Start small, flat stakes, keep a bet journal, avoid accumulators for fun, bet only markets you understand and watch +CLV.",
  'support.faq.ai.how.q': "How do AI football predictions work?",
  'support.faq.ai.how.a': "AI learns statistical patterns from historical match data and estimates probabilities for markets like 1X2, goals or BTTS.",
  'support.faq.ai.data.q': "What data is used for predictions?",
  'support.faq.ai.data.a': "Results, closing odds, Pi-Ratings, form, xG, lineups and optional Sofascore live data.",
  'support.faq.ai.reliability.q': "How reliable are AI predictions?",
  'support.faq.ai.reliability.a': "Good models beat the market by a few percentage points. They provide probabilities, not certainties — never expect 100% accuracy.",
  'support.faq.ai.model.q': "What is a prediction model?",
  'support.faq.ai.model.a': "A mathematical model that maps input features to an output probability, typically trained on historical matches.",
  'support.faq.ai.ml.q': "How is machine learning used in betting?",
  'support.faq.ai.ml.a': "ML learns non-linear patterns from features (form, xG, ratings) and predicts outcome probabilities — the basis for value-bet detection.",
  'support.faq.ai.features.q': "What are features in a model?",
  'support.faq.ai.features.a': "Features are numeric input variables like Pi-Rating delta, xG average, form score or market odds — the model's measurable signals.",
  'support.faq.ai.history.q': "How important is historical data?",
  'support.faq.ai.history.a': "Very important — at least 3–5 seasons per league so the model can learn stable patterns. Too little data leads to overfitting.",
  'support.faq.ai.oddsModel.q': "How does an odds model work?",
  'support.faq.ai.oddsModel.a': "An odds model derives implied probabilities from bookmaker odds (after margin removal) and compares them with its own prediction.",
  'support.faq.ai.valueBet.q': "How does AI detect value bets?",
  'support.faq.ai.valueBet.a': "The AI compares its calibrated probability p with market odds o. If p × o > 1 and the edge threshold is exceeded, the bet is flagged.",
  'support.faq.ai.overfitting.q': "How do you avoid overfitting?",
  'support.faq.ai.overfitting.a': "Walk-forward validation, regularisation (L2, early stopping), cross-validation and separate validation + holdout seasons.",
  'support.faq.ai.algorithms.q': "Which algorithms are suitable (e.g. Random Forest)?",
  'support.faq.ai.algorithms.a': "Gradient boosting (CatBoost, XGBoost), logistic regression as baseline, random forest and neural networks for non-linear patterns.",
  'support.faq.ai.liveData.q': "How do you integrate live data?",
  'support.faq.ai.liveData.a': "Via WebSocket or polling feeds (e.g. Sofascore, OpenLigaDB) current events like goals or cards are streamed into the model.",
  'support.faq.ai.realtime.q': "How important are real-time updates?",
  'support.faq.ai.realtime.a': "Critical for live betting and CLV tracking: a few seconds of delay can already shift the odds noticeably.",
  'support.faq.ai.measure.q': "How do you measure model accuracy?",
  'support.faq.ai.measure.a': "With Ranked Probability Score (RPS), Brier score, log-loss and calibration metrics like ECE — not just hit rate.",
  'support.faq.ai.improve.q': "How can you improve models?",
  'support.faq.ai.improve.a': "More/better features, hyperparameter tuning, calibration (Platt/isotonic), ensembling and regular retraining on fresh data.",
  'support.faq.ai.combine.q': "How do you combine multiple models?",
  'support.faq.ai.combine.a': "Via weighted probability averaging or a stacking meta-learner. Dirichlet tuning optimises the weights on a validation season.",
  'support.faq.ai.ensemble.q': "What is ensemble learning in betting?",
  'support.faq.ai.ensemble.a': "Multiple models (e.g. CatBoost + Poisson + MLP) are combined to cancel individual errors and produce more stable probabilities.",
  'support.faq.ai.apis.q': "How do you use APIs for data feeds?",
  'support.faq.ai.apis.a': "REST/WebSocket calls with rate-limit handling and caching (e.g. SQLite TTL) — authentication via API key header.",
  'support.faq.ai.dashboard.q': "How do you build a prediction dashboard?",
  'support.faq.ai.dashboard.a': "Backend exposes JSON snapshots, frontend (e.g. Next.js) renders probabilities, value bets and historical performance in cards/tables.",
  'support.faq.ai.automate.q': "How do you automate predictions?",
  'support.faq.ai.automate.a': "Cron jobs or GitHub Actions pull data each morning, train/score models and publish the snapshot to the API.",
  'support.faq.market.create.q': "How are odds created?",
  'support.faq.market.create.a': "Traders estimate probabilities, add the margin (overround) and adjust the odds based on incoming stake volume.",
  'support.faq.market.change.q': "Why do odds change?",
  'support.faq.market.change.a': "Odds react to team news, stake volume, sharp money and live events. Each new signal shifts the fair line.",
  'support.faq.market.clv.q': "What does Closing Line Value (CLV) mean?",
  'support.faq.market.clv.a': "CLV measures how much better your taken odds were versus the closing line. Positive CLV is the most reliable long-term profit indicator.",
  'support.faq.market.valueOdds.q': "How do I spot value in odds?",
  'support.faq.market.valueOdds.a': "Compute your own calibrated probability p and compare with market odds o: p × o > 1 → value. Strip margin first for fair prices.",
  'support.faq.market.bestBooks.q': "Which bookmakers offer the best odds?",
  'support.faq.market.bestBooks.a': "Sharp books like Pinnacle, Betfair (Exchange) or SBObet usually offer the lowest margins. Retail bookmakers tend to be pricier.",
  'support.faq.market.diffBooks.q': "Why do odds differ between operators?",
  'support.faq.market.diffBooks.a': "Different traders, margin strategies, target customers and risk profiles lead to slightly different fair-value estimates.",
  'support.faq.market.compare.q': "How do you use odds comparison tools?",
  'support.faq.market.compare.a': "Always take the best available price — even 2–3% extra odds boost ROI significantly. Oddsportal or Betexplorer are typical tools.",
  'support.faq.market.sharpPublic.q': "What is sharp vs public money?",
  'support.faq.market.sharpPublic.a': "Sharp money comes from profitable pros and moves the line durably. Public money backs favourites and popular teams, often without moving the price.",
  'support.faq.market.movement.q': "How do I spot market movements?",
  'support.faq.market.movement.a': "Track open-to-close odds movement and its speed. Sharp-driven moves are usually abrupt and against public sentiment.",
  'support.faq.market.liquidity.q': "How important is market liquidity?",
  'support.faq.market.liquidity.a': "Very important: liquid markets (Top-5 leagues) have tighter margins and more reliable closing lines. Niche leagues are volatile with less value.",
  'support.faq.profit.earn.q': "Can you make money from sports betting?",
  'support.faq.profit.earn.a': "Yes, but rarely and with great difficulty. Without a measurable edge, bankroll management and discipline only the bookmaker wins long-term.",
  'support.faq.profit.longterm.q': "What are the long-term winning chances?",
  'support.faq.profit.longterm.a': "Reliable estimates suggest only 2–5% of bettors are long-term profitable. A realistic ROI sits between 2% and 8%.",
  'support.faq.profit.roi.q': "What is a realistic ROI?",
  'support.faq.profit.roi.a': "A 2–5% ROI over thousands of bets is considered very good; 10%+ is extremely rare and usually short-term variance.",
  'support.faq.profit.timeToProfit.q': "How long does it take to become profitable?",
  'support.faq.profit.timeToProfit.a': "Typically several seasons and 1,000+ bets for the edge to stabilise and variance to wash out.",
  'support.faq.profit.capital.q': "How much capital do you need?",
  'support.faq.profit.capital.a': "Recommended: at least 100× the standard stake so normal losing runs don't wipe the bankroll. Only use money you can afford to lose.",
  'support.faq.profit.skillVsLuck.q': "Is sports betting gambling or skill?",
  'support.faq.profit.skillVsLuck.a': "Short-term it's variance, long-term it's a skill game — similar to poker. A measurable edge decides multi-year profitability.",
  'support.faq.profit.prosVsAmateurs.q': "How do pros differ from amateurs?",
  'support.faq.profit.prosVsAmateurs.a': "Pros have systems, models, bankroll rules and measure every edge. Amateurs bet emotionally, on favourites or accumulators.",
  'support.faq.profit.prosWork.q': "How do professional bettors work?",
  'support.faq.profit.prosWork.a': "Hours per day maintaining data, training models, scanning markets, placing bets and tracking CLV — it's a full-time job.",
  'support.faq.profit.patience.q': "How important is patience?",
  'support.faq.profit.patience.a': "Essential: even at 5% ROI variance produces multi-week drawdowns. Only the disciplined realise the edge long-term.",
  'support.faq.profit.fail90.q': "Why do 90% of bettors fail?",
  'support.faq.profit.fail90.a': "No system, no bankroll plan, emotional decisions, chasing, overbetting and misunderstanding of margin and variance.",
  'support.faq.platform.daily.q': "How do the daily predictions work?",
  'support.faq.platform.daily.a': "Each morning a snapshot is generated: load fixtures, build features, score the ensemble model, filter value bets and publish via API/frontend.",
  'support.faq.platform.autoload.q': "How are matches auto-loaded (API)?",
  'support.faq.platform.autoload.a': "Via Football-Data CSV feeds plus optional Sofascore API — cached and deduped by fixture ID to avoid duplicates.",
  'support.faq.platform.updateFreq.q': "How often should predictions be refreshed?",
  'support.faq.platform.updateFreq.a': "Daily pre-match by default, every 45–60 seconds on matchdays whenever odds or lineups change.",
  'support.faq.platform.confidence.q': "How do you display confidence scores?",
  'support.faq.platform.confidence.a': "As a probability (e.g. 62%) plus optional traffic-light categories (low/medium/high) derived from model entropy.",
  'support.faq.platform.visualize.q': "How do you visualise probabilities?",
  'support.faq.platform.visualize.a': "Stacked home/draw/away bars, percentage labels or radar charts. Keep the colours consistent (e.g. accent-blue for home).",
  'support.faq.platform.bestBets.q': "How do you filter 'best bets of the day'?",
  'support.faq.platform.bestBets.a': "Combine positive edge, a minimum confidence threshold and a minimum odds level, then sort by Kelly fraction descending.",
  'support.faq.platform.history.q': "How do you show historical performance?",
  'support.faq.platform.history.a': "On a track-record page showing ROI, strike rate, CLV, Brier/RPS and a rolling P&L chart of the last 200+ bets.",
  'support.faq.platform.tracking.q': "How do you integrate user tracking?",
  'support.faq.platform.tracking.a': "Consent-based with a lightweight analytics tool (e.g. Plausible), anonymised and only after explicit cookie consent.",
  'support.faq.platform.ranking.q': "How do you build a ranking system for tips?",
  'support.faq.platform.ranking.a': "Sort by a composite score of edge × confidence × liquidity, with a minimum number of past bets per tipster/model.",
  'support.faq.platform.lastBets.q': "How do you correctly implement 'last bets' logic?",
  'support.faq.platform.lastBets.a': "Sort by placement timestamp (not kickoff), filter on settled fixtures and 1:1-join each bet with its final result by fixture ID.",
  'support.faq.platform.wrongMatch.q': "How do you prevent wrong-match bugs?",
  'support.faq.platform.wrongMatch.a': "Use a single fixture ID as primary key across layers, validate home/away order against the snapshot source and test with snapshot fixtures.",
  'support.faq.platform.valueVsPrediction.q': "How do you differentiate value bets vs predictions?",
  'support.faq.platform.valueVsPrediction.a': "Predictions = outcome probabilities. Value bets = subset with positive edge versus the market. Not every prediction is bet-worthy.",
  'support.faq.platform.alerts.q': "How do you build user alerts?",
  'support.faq.platform.alerts.a': "Push or email triggers on edge above threshold, odds movement or new high-confidence picks — always opt-in with a frequency cap.",
  'support.faq.platform.trust.q': "How do you build trust in the platform?",
  'support.faq.platform.trust.a': "A public, immutable track-record log, transparent methodology, clear calibration metrics and responsible-gambling messaging.",


  // <BEGIN_FOLLOWUP_STRINGS>
  'support.faq.valueBet.fq': "How do I actually verify a bet has positive expected value before placing it?",
  'support.faq.valueBet.fa': "Convert the decimal odds to implied probability (1 / odds), divide by the sum of implied probabilities across all outcomes to strip out the bookmaker's overround, then compare against your model probability. Only when model probability x odds is greater than 1.02 — a small safety buffer beyond zero EV — is the edge real after slippage and commission.",
  'support.faq.accuracy.fq': "What does an RPS of 0.20 actually mean for my betting decisions?",
  'support.faq.accuracy.fa': "RPS measures the squared distance between predicted and actual outcome across all three results — 0.20 leaves us roughly two percentage points better-calibrated than implied bookmaker odds (~0.22). In practice that translates to a 1–3% ROI edge on selectively chosen bets, but only after fair-odds adjustment and disciplined Kelly sizing.",
  'support.faq.dataSource.fq': "Why don't you use a paid live odds API for in-play prices?",
  'support.faq.dataSource.fa': "Closing odds from Football-Data are sufficient to measure CLV and train the calibration layer, and Sofascore covers the lineup and xG signals we need pre-match. A live in-play feed would add latency-arbitrage complexity without improving pre-match calibration — and that is precisely where our edge sits.",
  'support.faq.snapshotUpdate.fq': "Should I act on a value bet right at snapshot publish time or wait until the afternoon?",
  'support.faq.snapshotUpdate.fa': "Early-morning value bets often vanish within hours because sharp money moves the line, so log them immediately at the displayed odds if you're going to take them. After roughly 16:00 local kickoff time the prices stabilise and any remaining edge is much more likely to be a true mispricing than stale snapshot data.",
  'support.faq.kelly.fq': "When should I deviate from the suggested quarter-Kelly stake?",
  'support.faq.kelly.fa': "Drop to one-eighth Kelly when your bankroll has fallen more than 20% from peak (drawdown protection) or when calibration on the league is below average that month. Never push above half-Kelly even on highest-confidence bets — variance kills bankrolls faster than the missed upside is worth.",
  'support.faq.piRating.fq': "What is the most important next step on this topic?",
  'support.faq.piRating.fa': "Apply the concept to a concrete example, compare your result to a reference value and track the outcome over at least 50 decisions before adjusting behaviour.",
  'support.faq.responsible.fq': "What is the most important next step on this topic?",
  'support.faq.responsible.fa': "Apply the concept to a concrete example, compare your result to a reference value and track the outcome over at least 50 decisions before adjusting behaviour.",
  'support.faq.language.fq': "What is the most important next step on this topic?",
  'support.faq.language.fa': "Apply the concept to a concrete example, compare your result to a reference value and track the outcome over at least 50 decisions before adjusting behaviour.",
  'support.faq.cookies.fq': "What is the most important next step on this topic?",
  'support.faq.cookies.fa': "Apply the concept to a concrete example, compare your result to a reference value and track the outcome over at least 50 decisions before adjusting behaviour.",
  'support.faq.contact.fq': "What is the most important next step on this topic?",
  'support.faq.contact.fa': "Apply the concept to a concrete example, compare your result to a reference value and track the outcome over at least 50 decisions before adjusting behaviour.",
  'support.faq.basics.oneX2.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.oneX2.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.odds.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.odds.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.winnings.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.winnings.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.single.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.single.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.accumulator.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.accumulator.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.system.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.system.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.valueBetBasic.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.valueBetBasic.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.probability.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.probability.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.bookie.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.bookie.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.bookieMoney.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.bookieMoney.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.overround.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.overround.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.live.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.live.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.cashout.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.cashout.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.handicap.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.handicap.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.asianHandicap.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.asianHandicap.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.ou25.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.ou25.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.btts.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.btts.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.dnb.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.dnb.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.doubleChance.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.doubleChance.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.basics.specials.fq': "When is this market actually the smart choice in practice?",
  'support.faq.basics.specials.fa': "Pick this market when your model probability clearly beats the bookmaker's implied probability and the overround is below 6%. Switch to single-outcome markets when liquidity is thin or the line is late.",
  'support.faq.analysis.howTo.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.howTo.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.stats.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.stats.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.form.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.form.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.homeAway.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.homeAway.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.injuries.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.injuries.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.lineups.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.lineups.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.xg.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.xg.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.h2h.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.h2h.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.motivation.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.motivation.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.weather.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.weather.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.defOff.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.defOff.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.goalStats.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.goalStats.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.bestLeague.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.bestLeague.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.coach.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.coach.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.tempo.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.tempo.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.ouGames.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.ouGames.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.bttsGames.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.bttsGames.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.draws.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.draws.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.underdogs.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.underdogs.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.analysis.trapGames.fq': "Which concrete signals carry the most weight here?",
  'support.faq.analysis.trapGames.fa': "Prioritise stable indicators: xG differential over the last 8 matches, adjusted Pi-ratings, and the gap between opening and closing line value. Never rely on a single metric — combine at least three signals.",
  'support.faq.strategy.best.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.best.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.valueBet.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.valueBet.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.arbitrage.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.arbitrage.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.martingale.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.martingale.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.flat.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.flat.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.bankroll.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.bankroll.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.stake.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.stake.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.losingStreak.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.losingStreak.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.combos.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.combos.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.profitable.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.profitable.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.test.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.test.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.roi.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.roi.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.strikeRate.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.strikeRate.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.discipline.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.discipline.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.goodOdds.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.goodOdds.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.noBet.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.noBet.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.timing.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.timing.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.prematchLive.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.prematchLive.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.oddsMovement.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.oddsMovement.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.strategy.ownSystem.fq': "How do you execute this strategy in practice with discipline?",
  'support.faq.strategy.ownSystem.fa': "Lock in stake size (1–3% of bankroll), edge threshold (3% minimum) and exit rule in advance. Log every bet with pre-match odds and compare to the close — that is the only way to prove the edge is real, not luck.",
  'support.faq.mistakes.loseMoney.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.loseMoney.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.chasing.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.chasing.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.emotions.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.emotions.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.accumulators.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.accumulators.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.overbetting.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.overbetting.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.tipsters.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.tipsters.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.noBankroll.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.noBankroll.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.sureBets.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.sureBets.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.favTeam.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.favTeam.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.mistakes.beginner.fq': "How do you concretely avoid this mistake in your daily routine?",
  'support.faq.mistakes.beginner.fa': "Build guardrails: fixed weekly limits, a 24-hour cool-down after losses and a public bet log. If you break a limit, pause without exception — please use the responsible-gambling tools on the site if control slips.",
  'support.faq.ai.how.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.how.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.data.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.data.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.reliability.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.reliability.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.model.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.model.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.ml.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.ml.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.features.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.features.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.history.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.history.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.oddsModel.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.oddsModel.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.valueBet.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.valueBet.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.overfitting.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.overfitting.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.algorithms.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.algorithms.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.liveData.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.liveData.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.realtime.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.realtime.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.measure.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.measure.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.improve.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.improve.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.combine.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.combine.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.ensemble.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.ensemble.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.apis.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.apis.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.dashboard.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.dashboard.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.ai.automate.fq': "Where are the limits of this AI approach?",
  'support.faq.ai.automate.fa': "Models fail on rare events (cup upsets, post-coach-change regime shifts) and when market features are dominated by insider information. That is why calibration via isotonic/Platt and drift monitoring with a KS-test are mandatory.",
  'support.faq.market.create.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.create.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.change.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.change.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.clv.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.clv.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.valueOdds.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.valueOdds.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.bestBooks.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.bestBooks.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.diffBooks.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.diffBooks.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.compare.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.compare.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.sharpPublic.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.sharpPublic.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.movement.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.movement.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.market.liquidity.fq': "How do you turn this market observation into an actual bet?",
  'support.faq.market.liquidity.fa': "Compare the early price (T-24h) to the closing line across at least three bookmakers. If your bets regularly show positive CLV, the market is validating your edge — a stronger quality signal than short-term hit rate.",
  'support.faq.profit.earn.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.earn.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.longterm.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.longterm.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.roi.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.roi.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.timeToProfit.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.timeToProfit.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.capital.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.capital.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.skillVsLuck.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.skillVsLuck.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.prosVsAmateurs.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.prosVsAmateurs.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.prosWork.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.prosWork.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.patience.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.patience.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.profit.fail90.fq': "What are the realistic expectations you should hold here?",
  'support.faq.profit.fail90.fa': "Realistic numbers are 2–5% ROI over at least 500 bets for disciplined value players — with interim drawdowns of 20% or more. Anyone expecting faster 'profit' is underestimating sports-betting variance.",
  'support.faq.platform.daily.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.daily.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.autoload.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.autoload.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.updateFreq.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.updateFreq.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.confidence.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.confidence.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.visualize.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.visualize.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.bestBets.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.bestBets.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.history.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.history.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.tracking.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.tracking.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.ranking.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.ranking.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.lastBets.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.lastBets.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.wrongMatch.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.wrongMatch.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.valueVsPrediction.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.valueVsPrediction.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.alerts.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.alerts.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.platform.trust.fq': "Where exactly do you find this information in the platform?",
  'support.faq.platform.trust.fa': "The Today view shows the current snapshot with a timestamp; the Performance page exposes RPS, Brier and ROI per league; the Leagues page lists Pi-ratings. All raw data is published as JSON under data/snapshots/.",
  'support.faq.valueBet.alt1': "Does this bet have positive expected value?",
  'support.faq.valueBet.alt2': "Where is the edge on this one?",
  'support.faq.valueBet.alt3': "Is this a +EV bet?",
  'support.faq.valueBet.alt4': "Is the bet mathematically worth it?",
  'support.faq.valueBet.alt5': "Is the bookmaker pricing this wrong?",
  'support.faq.accuracy.alt1': "How accurate is your model really?",
  'support.faq.accuracy.alt2': "What is the hit rate of the AI?",
  'support.faq.accuracy.alt3': "How reliable are the predictions?",
  'support.faq.accuracy.alt4': "Can I trust the forecasts?",
  'support.faq.accuracy.alt5': "Is accuracy better than the bookmakers?",
  'support.faq.dataSource.alt1': "Where does your data come from?",
  'support.faq.dataSource.alt2': "Which sources does the platform use?",
  'support.faq.dataSource.alt3': "Is the data official?",
  'support.faq.dataSource.alt4': "How fresh are your result feeds?",
  'support.faq.dataSource.alt5': "Are the odds pulled live from bookmakers?",
  'support.faq.snapshotUpdate.alt1': "When does the snapshot get refreshed?",
  'support.faq.snapshotUpdate.alt2': "How often do new tips appear?",
  'support.faq.snapshotUpdate.alt3': "At what time are the predictions published?",
  'support.faq.snapshotUpdate.alt4': "Is today's snapshot already current?",
  'support.faq.snapshotUpdate.alt5': "What is the publishing cadence?",
  'support.faq.kelly.alt1': "How much should I stake?",
  'support.faq.kelly.alt2': "What's the optimal bet size?",
  'support.faq.kelly.alt3': "How much of my bankroll should I risk?",
  'support.faq.kelly.alt4': "Recommended stake size",
  'support.faq.kelly.alt5': "What size should I pick for this bet?",
  'support.faq.piRating.alt1': "How strong is this team?",
  'support.faq.piRating.alt2': "Which team is the better opponent?",
  'support.faq.piRating.alt3': "How is team strength calculated?",
  'support.faq.piRating.alt4': "Which side is the favourite?",
  'support.faq.piRating.alt5': "What's a team's Pi-Rating value?",
  'support.faq.responsible.alt1': "Is this gambling safe?",
  'support.faq.responsible.alt2': "Can I become addicted?",
  'support.faq.responsible.alt3': "Help with gambling addiction",
  'support.faq.responsible.alt4': "Is this financial advice?",
  'support.faq.responsible.alt5': "Am I gambling responsibly?",
  'support.faq.language.alt1': "Change language",
  'support.faq.language.alt2': "Switch to English",
  'support.faq.language.alt3': "Where are the language settings?",
  'support.faq.language.alt4': "How do I pick a different locale?",
  'support.faq.language.alt5': "Is the site available in my language?",
  'support.faq.cookies.alt1': "What cookies do you set?",
  'support.faq.cookies.alt2': "Withdraw cookie consent",
  'support.faq.cookies.alt3': "Disable tracking",
  'support.faq.cookies.alt4': "Cookie privacy policy",
  'support.faq.cookies.alt5': "Do you store my data?",
  'support.faq.contact.alt1': "How can I reach you?",
  'support.faq.contact.alt2': "Contact support",
  'support.faq.contact.alt3': "What's your email address?",
  'support.faq.contact.alt4': "How do I file a help request?",
  'support.faq.contact.alt5': "Where can I find support?",
  'support.faq.basics.oneX2.alt1': "What does 1X2 mean?",
  'support.faq.basics.oneX2.alt2': "Three-way bet explained",
  'support.faq.basics.oneX2.alt3': "Home win, draw, away win — how?",
  'support.faq.basics.oneX2.alt4': "How does the 1X2 market work?",
  'support.faq.basics.oneX2.alt5': "Explain the 1X2 market",
  'support.faq.basics.odds.alt1': "How do I read odds?",
  'support.faq.basics.odds.alt2': "What are decimal odds?",
  'support.faq.basics.odds.alt3': "What does odds of 2.50 mean?",
  'support.faq.basics.odds.alt4': "Understanding odds",
  'support.faq.basics.odds.alt5': "Convert odds to probability",
  'support.faq.basics.winnings.alt1': "How do I calculate winnings?",
  'support.faq.basics.winnings.alt2': "Payout formula",
  'support.faq.basics.winnings.alt3': "How much do I get back?",
  'support.faq.basics.winnings.alt4': "What will I win?",
  'support.faq.basics.winnings.alt5': "Compute profit from odds",
  'support.faq.basics.single.alt1': "What's a single bet?",
  'support.faq.basics.single.alt2': "Single bet explained",
  'support.faq.basics.single.alt3': "What does a single mean?",
  'support.faq.basics.single.alt4': "Bet on just one game",
  'support.faq.basics.single.alt5': "Advantage of singles",
  'support.faq.basics.accumulator.alt1': "What's an accumulator?",
  'support.faq.basics.accumulator.alt2': "How does a parlay work?",
  'support.faq.basics.accumulator.alt3': "Combine multiple games into one bet",
  'support.faq.basics.accumulator.alt4': "Accumulator explained",
  'support.faq.basics.accumulator.alt5': "Combine several tips",
  'support.faq.basics.system.alt1': "What's a system bet?",
  'support.faq.basics.system.alt2': "System bet explained",
  'support.faq.basics.system.alt3': "How does a 2-from-3 system work?",
  'support.faq.basics.system.alt4': "System bet example",
  'support.faq.basics.system.alt5': "Advantage of system bets",
  'support.faq.basics.valueBetBasic.alt1': "What's a value bet for beginners?",
  'support.faq.basics.valueBetBasic.alt2': "Good tip for today",
  'support.faq.basics.valueBetBasic.alt3': "Where do I find value?",
  'support.faq.basics.valueBetBasic.alt4': "How to spot a +EV bet?",
  'support.faq.basics.valueBetBasic.alt5': "Is this odd worth it?",
  'support.faq.basics.probability.alt1': "What's implied probability?",
  'support.faq.basics.probability.alt2': "Convert odds to percentage",
  'support.faq.basics.probability.alt3': "Calculate probability from odds",
  'support.faq.basics.probability.alt4': "What does a 60% chance mean?",
  'support.faq.basics.probability.alt5': "Implied probability explained",
  'support.faq.basics.bookie.alt1': "What's a bookmaker?",
  'support.faq.basics.bookie.alt2': "Which bookie is good?",
  'support.faq.basics.bookie.alt3': "Betting provider explained",
  'support.faq.basics.bookie.alt4': "Bookmaker recommendation",
  'support.faq.basics.bookie.alt5': "How to choose a bookie",
  'support.faq.basics.bookieMoney.alt1': "How do bookmakers make money?",
  'support.faq.basics.bookieMoney.alt2': "Why does the bookie always win?",
  'support.faq.basics.bookieMoney.alt3': "Bookmaker margin explained",
  'support.faq.basics.bookieMoney.alt4': "Does the bookie profit from me?",
  'support.faq.basics.bookieMoney.alt5': "Bookmaker business model",
  'support.faq.basics.overround.alt1': "What is overround?",
  'support.faq.basics.overround.alt2': "Calculate bookmaker margin",
  'support.faq.basics.overround.alt3': "Vig explained",
  'support.faq.basics.overround.alt4': "How big is the margin on a market?",
  'support.faq.basics.overround.alt5': "Juice in odds",
  'support.faq.basics.live.alt1': "What's a live bet?",
  'support.faq.basics.live.alt2': "In-play betting explained",
  'support.faq.basics.live.alt3': "Bet live during the match",
  'support.faq.basics.live.alt4': "Live odds keep changing",
  'support.faq.basics.live.alt5': "Pros and cons of live bets",
  'support.faq.basics.cashout.alt1': "What is cashout?",
  'support.faq.basics.cashout.alt2': "Cash out a bet early",
  'support.faq.basics.cashout.alt3': "Is cash-out worth it?",
  'support.faq.basics.cashout.alt4': "Cashout feature explained",
  'support.faq.basics.cashout.alt5': "When should I cash out?",
  'support.faq.basics.handicap.alt1': "What's a handicap bet?",
  'support.faq.basics.handicap.alt2': "Spread bet explained",
  'support.faq.basics.handicap.alt3': "What does +1 handicap mean?",
  'support.faq.basics.handicap.alt4': "When to use handicap?",
  'support.faq.basics.handicap.alt5': "Understanding the handicap market",
  'support.faq.basics.asianHandicap.alt1': "What's an Asian handicap?",
  'support.faq.basics.asianHandicap.alt2': "AH +0.5 explained",
  'support.faq.basics.asianHandicap.alt3': "Quarter handicap explained",
  'support.faq.basics.asianHandicap.alt4': "Asian handicap vs regular handicap",
  'support.faq.basics.asianHandicap.alt5': "When is AH worth it?",
  'support.faq.basics.ou25.alt1': "What does Over/Under 2.5 mean?",
  'support.faq.basics.ou25.alt2': "Over 2.5 goals bet",
  'support.faq.basics.ou25.alt3': "Low-scoring bet",
  'support.faq.basics.ou25.alt4': "Over Under explained",
  'support.faq.basics.ou25.alt5': "When to bet Over 2.5?",
  'support.faq.basics.btts.alt1': "What is BTTS?",
  'support.faq.basics.btts.alt2': "Both teams to score bet",
  'support.faq.basics.btts.alt3': "GG tip explained",
  'support.faq.basics.btts.alt4': "Both Teams to Score explained",
  'support.faq.basics.btts.alt5': "When to bet BTTS?",
  'support.faq.basics.dnb.alt1': "What is Draw No Bet?",
  'support.faq.basics.dnb.alt2': "DNB explained",
  'support.faq.basics.dnb.alt3': "Bet with no draw risk",
  'support.faq.basics.dnb.alt4': "Stake back on a draw",
  'support.faq.basics.dnb.alt5': "When is DNB worth it?",
  'support.faq.basics.doubleChance.alt1': "What is Double Chance?",
  'support.faq.basics.doubleChance.alt2': "Double chance explained",
  'support.faq.basics.doubleChance.alt3': "1X or X2 bet",
  'support.faq.basics.doubleChance.alt4': "Bet on not losing",
  'support.faq.basics.doubleChance.alt5': "When to use double chance?",
  'support.faq.basics.specials.alt1': "What are special bets?",
  'support.faq.basics.specials.alt2': "Who scores the first goal?",
  'support.faq.basics.specials.alt3': "First scorer bet explained",
  'support.faq.basics.specials.alt4': "Examples of prop bets",
  'support.faq.basics.specials.alt5': "Special markets explained",
  // <END_FOLLOWUP_STRINGS>

};
