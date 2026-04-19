import type { Dictionary } from './en';

export const it: Dictionary = {
  'site.title': 'Betting with AI',
  'site.tagline':
    'Analisi di scommesse calcistiche basate sull’IA per i top 5 campionati.',
  'site.description':
    'Pronostici calcistici e value bet basati sui dati per Premier League, Bundesliga, Serie A, Liga ed EFL Championship. Ensemble CatBoost + Poisson + MLP con monitoraggio trasparente delle performance.',
  'home.heading': 'Analisi di scommesse di oggi per i top 5 campionati.',
  'home.subheading':
    'Probabilità calibrate per 1, X e 2 — più value bet quando il modello diverge dal mercato.',
  'home.loading': 'Caricamento dei pronostici…',
  'home.section.valueBets.title': 'Value Bet',
  'home.section.valueBets.caption':
    'Discrepanze rilevate tra modello e mercato.',
  'home.section.valueBets.empty.title': 'Nessuna value bet al momento',
  'home.section.valueBets.empty.hint':
    'Quando il modello individua un vantaggio significativo sul mercato, le opportunità appariranno qui.',
  'home.section.predictions.title': 'Pronostici di oggi',
  'home.section.predictions.caption': 'Probabilità per 1 · X · 2.',
  'home.section.predictions.empty.title': 'Nessun pronostico disponibile',
  'home.section.predictions.empty.hint':
    'Genera uno snapshot con `fb snapshot` o inserisci un file di partite in “data/”.',
  'leagues.label': 'Campionati',
  'leagues.heading': 'Pi-Ratings e forma in ogni grande campionato.',
  'leagues.description':
    'Pi-Ratings, forma recente e scontri diretti per Premier League, Bundesliga, Serie A, Liga ed EFL Championship.',
  'leagues.teams': '{n} squadre',
  'leagues.leader': 'Leader:',
  'leagues.noData': 'Nessun dato — esegui `fb download`.',
  'leagues.viewDetails': 'Vedi dettagli →',
  'league.back': '← Tutti i campionati',
  'league.subtitle':
    'Pi-Ratings secondo Constantinou & Fenton (2013) — separati per forza in casa e in trasferta.',
  'league.section.table': 'Classifica',
  'league.empty.title': 'Nessun dato',
  'league.empty.hint':
    'Carica i dati del campionato con `fb download --league all`.',
  'performance.label': 'Trasparenza del modello',
  'performance.heading': 'Performance sull’intero storico delle scommesse.',
  'performance.description':
    'Piena trasparenza su win rate, ROI, drawdown massimo e analisi per campionato — aggiornati dopo ogni giornata.',
  'performance.section.coreMetrics': 'Metriche chiave',
  'performance.section.bankroll': 'Curva di bankroll',
  'performance.section.bankroll.caption': 'Bankroll iniziale 1.000.',
  'performance.section.byLeague': 'Analisi per campionato',
  'performance.byLeague.empty':
    'Ancora nessuna scommessa regolata per campionato.',
  'performance.byLeague.col.league': 'Campionato',
  'performance.byLeague.col.name': 'Nome',
  'performance.byLeague.col.bets': 'Scommesse',
  'performance.byLeague.col.hitRate': 'Win rate',
  'performance.byLeague.col.roi': 'ROI',
  'kpi.bets': 'Scommesse',
  'kpi.bets.hint': '{n} pronostici totali',
  'kpi.hitRate': 'Win rate',
  'kpi.hitRate.noBets': 'Ancora nessuna scommessa regolata',
  'kpi.hitRate.hint': 'Vincite / scommesse regolate',
  'kpi.roi': 'ROI',
  'kpi.maxDrawdown': 'Drawdown max.',
  'transparency.title': 'Tracker di trasparenza',
  'transparency.updating':
    'I dati di performance sono in aggiornamento.',
  'transparency.disclaimer':
    'Simulazione ipotetica di un modello statistico basato su dati storici delle partite. Non è un invito a scommettere. Nessuna garanzia di risultati futuri. Il gioco comporta rischi finanziari.',
  'transparency.viewFullDetails': 'Vedi tutti i dettagli',
  'recentBets.title': 'Scommesse recenti',
  'recentBets.captionFallback': 'Valutazione delle value bet passate',
  'recentBets.captionTemplate':
    'Ultimi {n} {dayLabel} · {bets} scommesse · Win rate {rate}',
  'recentBets.day.bet': 'Scommessa',
  'recentBets.day.bets': 'Scommesse',
  'recentBets.day.day': 'giorno',
  'recentBets.day.days': 'giorni',
  'recentBets.day.pending': '{n} in sospeso',
  'recentBets.status.won': 'Vinta',
  'recentBets.status.lost': 'Persa',
  'recentBets.status.pending': 'In sospeso',
  'recentBets.empty.title': 'Ancora nessuna scommessa regolata',
  'recentBets.empty.hint':
    'Appena finiranno le prime partite, i risultati appariranno qui con valutazione verde/rossa.',
  'recentBets.updating': 'La cronologia è in aggiornamento.',
  'predictionCard.outcome.home': 'Vittoria casa',
  'predictionCard.outcome.draw': 'Pareggio',
  'predictionCard.outcome.away': 'Vittoria trasferta',
  'predictionCard.pick': 'Scelta:',
  'predictionCard.vs': 'vs',
  'valueBet.confidence.high': 'Alta',
  'valueBet.confidence.medium': 'Media',
  'valueBet.confidence.low': 'Bassa',
  'valueBet.odds': 'Quota',
  'valueBet.edge': 'Edge',
  'valueBet.stake': 'Puntata',
  'bankroll.empty':
    'Nessun dato di bankroll — registra delle scommesse per iniziare il monitoraggio.',
  'ratings.col.team': 'Squadra',
  'ratings.col.home': 'Casa',
  'ratings.col.away': 'Trasferta',
  'ratings.col.overall': 'Totale',
  'ratings.col.form': 'Forma',
  'nav.today': 'Oggi',
  'nav.performance': 'Performance',
  'nav.leagues': 'Campionati',
  'nav.language': 'Lingua',
  'footer.text':
    'Betting with AI · Ensemble CatBoost + Poisson + MLP · Modello v0.3',
  'cookie.title': 'Utilizziamo i cookie',
  'cookie.body':
    'Questo sito utilizza cookie e tecnologie simili per garantirne il funzionamento e per misurare audience e performance. Il tuo consenso viene memorizzato insieme a un hash del tuo indirizzo IP, così da riconoscerlo alla tua prossima visita. Puoi revocarlo in qualsiasi momento.',
  'cookie.necessary.title': 'Necessari',
  'cookie.necessary.desc':
    'Indispensabili per il funzionamento del sito. Sempre attivi.',
  'cookie.analytics.title': 'Statistiche',
  'cookie.analytics.desc':
    'Misurazione anonima dell’uso per migliorare il sito.',
  'cookie.marketing.title': 'Marketing',
  'cookie.marketing.desc':
    'Contenuti personalizzati e tracciamento di terze parti.',
  'cookie.btn.settings': 'Impostazioni',
  'cookie.btn.hideDetails': 'Nascondi dettagli',
  'cookie.btn.reject': 'Rifiuta',
  'cookie.btn.save': 'Salva selezione',
  'cookie.btn.acceptAll': 'Accetta tutto',
  'cookie.aria.dialog': 'Consenso ai cookie',
};
