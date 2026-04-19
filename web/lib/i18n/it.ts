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
  'nav.about': 'Chi siamo',
  'nav.methodology': 'Metodologia',
  'footer.text':
    'Betting with AI · Ensemble CatBoost + Poisson + MLP · Modello v0.3',
  'footer.col.product': 'Prodotto',
  'footer.col.about': 'Chi siamo',
  'footer.col.legal': 'Note legali',
  'footer.col.responsible': 'Gioco responsabile',
  'footer.link.today': 'Pronostici di oggi',
  'footer.link.leagues': 'Campionati',
  'footer.link.performance': 'Tracker delle performance',
  'footer.link.about': 'Chi siamo',
  'footer.link.methodology': 'Metodologia',
  'footer.link.changelog': 'Changelog del modello',
  'footer.link.terms': 'Termini di servizio',
  'footer.link.privacy': 'Informativa sulla privacy',
  'footer.link.cookies': 'Cookie',
  'footer.link.impressum': 'Note legali',
  'footer.link.responsibleGambling': 'Gioco responsabile',
  'footer.link.helpline': 'Telefono Verde Nazionale Dipendenze (IT)',
  'footer.disclaimer':
    "Contenuti solo informativi. Nessun consiglio di scommessa. Non accettiamo puntate e non percepiamo commissioni dai bookmaker. Le performance passate del modello non garantiscono risultati futuri.",
  'footer.ageBadge.label': '18+ · Solo informativo',
  'page.about.title': 'Chi siamo · Betting with AI',
  'page.about.description':
    "Analitica calcistica IA indipendente e senza affiliazioni, costruita da un singolo data scientist. Perché esistiamo, chi siamo e in cosa differiamo dai siti di pronostici affiliati.",
  'page.methodology.title': 'Metodologia · Come funziona il nostro modello',
  'page.methodology.description':
    'Pi-Ratings, CatBoost, Poisson Dixon-Coles, ensemble MLP, calibrazione isotonica e backtest walk-forward — ogni componente spiegato in modo trasparente.',
  'page.responsibleGambling.title': 'Gioco responsabile',
  'page.responsibleGambling.description':
    'Aiuto, autoesclusione e numeri verdi nazionali contro la dipendenza dal gioco in Italia, Regno Unito, Germania, Francia e Spagna.',
  'page.terms.title': 'Termini di servizio',
  'page.terms.description':
    'Condizioni legali per l’uso di Betting with AI. Contenuti puramente editoriali — non siamo un bookmaker e non accettiamo scommesse.',
  'page.privacy.title': 'Informativa sulla privacy',
  'page.privacy.description':
    'Come Betting with AI tratta dati personali, cookie e analytics ai sensi del GDPR.',
  'page.cookies.title': 'Informativa sui cookie',
  'page.cookies.description':
    'Quali cookie impostiamo, perché e come gestire le tue preferenze.',
  'page.impressum.title': 'Note legali',
  'page.impressum.description':
    'Informazioni legali sull’editore del sito Betting with AI.',
  'page.trackRecord.title': 'Track Record · Accuratezza verificata',
  'page.trackRecord.description':
    'Storico pubblico e scaricabile di ogni pronostico Betting with AI confrontato con il risultato effettivo, con grafico di calibrazione e download CSV. Niente cherry-picking.',
  'page.learn.title': 'Impara · Concetti di scommesse calcio',
  'page.learn.description':
    'Guide chiare a value bet, expected goals, criterio di Kelly, calibrazione del modello e altro — da un analista IA indipendente di calcio.',
  'trackRecord.calibration.title': 'Grafico di calibrazione',
  'trackRecord.calibration.caption':
    'Probabilità prevista vs frequenza osservata su tutti i risultati conclusi. La diagonale è la calibrazione perfetta.',
  'trackRecord.csv.title': 'Scarica il dataset completo',
  'trackRecord.csv.caption':
    'Ogni pronostico, con le probabilità del modello, il risultato reale e un flag di correttezza. CSV, UTF-8.',
  'trackRecord.csv.button': 'Scarica track-record.csv',
  'trackRecord.stats.records': 'Pronostici registrati',
  'trackRecord.stats.settled': 'Conclusi (con risultato)',
  'learn.heading': 'Concetti delle scommesse calcio, spiegati con chiarezza.',
  'learn.intro':
    'Guide brevi e basate sui dati su value bet, calibrazione del modello, gestione del bankroll e le metriche con cui questo sito viene giudicato.',
  'learn.readMore': 'Leggi →',
  'leagueHub.next5.title': 'Prossime 5 partite',
  'leagueHub.next5.empty': 'Nessuna partita imminente nello snapshot attuale.',
  'leagueHub.last5.title': 'Ultimi 5 risultati',
  'leagueHub.last5.empty': 'Nessun risultato recente disponibile.',
  'leagueHub.pickCorrect': 'Pronostico corretto',
  'leagueHub.pickIncorrect': 'Pronostico errato',
  'leagueHub.viewMatch': 'Apri pronostico →',
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
