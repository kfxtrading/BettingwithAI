import type { Dictionary } from './en';

export const es: Dictionary = {
  'site.title': 'Betting with AI',
  'site.tagline':
    'Análisis de apuestas de fútbol impulsados por IA para las cinco grandes ligas.',
  'site.description':
    'Pronósticos de fútbol y value bets basados en datos para la Premier League, Bundesliga, Serie A, LaLiga y EFL Championship. Ensamble CatBoost + Poisson + MLP con seguimiento de rendimiento transparente.',
  'home.heading': 'Análisis de apuestas de hoy para las cinco grandes ligas.',
  'home.subheading':
    'Probabilidades calibradas para Local, Empate y Visitante — más value bets cuando el modelo discrepa del mercado.',
  'home.loading': 'Cargando pronósticos…',
  'home.section.valueBets.title': 'Value Bets',
  'home.section.valueBets.caption':
    'Discrepancias detectadas entre el modelo y el mercado.',
  'home.section.valueBets.empty.title': 'Sin value bets por ahora',
  'home.section.valueBets.empty.hint':
    'Cuando el modelo encuentre una ventaja significativa sobre el mercado, las oportunidades aparecerán aquí.',
  'home.section.predictions.title': 'Pronósticos de hoy',
  'home.section.predictions.caption':
    'Probabilidades para Local · Empate · Visitante.',
  'home.section.predictions.empty.title': 'Sin pronósticos disponibles',
  'home.section.predictions.empty.hint':
    'Genera un snapshot con `fb snapshot` o coloca un archivo de partidos en «data/».',
  'leagues.label': 'Ligas',
  'leagues.heading': 'Pi-Ratings y forma en todas las grandes ligas.',
  'leagues.description':
    'Pi-Ratings, forma reciente y enfrentamientos directos para la Premier League, Bundesliga, Serie A, LaLiga y EFL Championship.',
  'leagues.teams': '{n} equipos',
  'leagues.leader': 'Líder:',
  'leagues.noData': 'Aún no hay datos — ejecuta `fb download`.',
  'leagues.viewDetails': 'Ver detalles →',
  'league.back': '← Todas las ligas',
  'league.subtitle':
    'Pi-Ratings según Constantinou & Fenton (2013) — separados por fuerza local y visitante.',
  'league.section.table': 'Tabla',
  'league.empty.title': 'Sin datos',
  'league.empty.hint':
    'Carga los datos de la liga con `fb download --league all`.',
  'performance.label': 'Transparencia del modelo',
  'performance.heading':
    'Rendimiento sobre todo el histórico de apuestas.',
  'performance.description':
    'Transparencia total sobre tasa de acierto, ROI, drawdown máximo y desglose por liga — actualizado después de cada jornada.',
  'performance.section.coreMetrics': 'Métricas clave',
  'performance.section.bankroll': 'Curva de bankroll',
  'performance.section.bankroll.caption': 'Bankroll inicial 1.000.',
  'performance.section.byLeague': 'Desglose por liga',
  'performance.byLeague.empty':
    'Aún no hay apuestas liquidadas por liga.',
  'performance.byLeague.col.league': 'Liga',
  'performance.byLeague.col.name': 'Nombre',
  'performance.byLeague.col.bets': 'Apuestas',
  'performance.byLeague.col.hitRate': 'Tasa de acierto',
  'performance.byLeague.col.roi': 'ROI',
  'kpi.bets': 'Apuestas',
  'kpi.bets.hint': '{n} pronósticos en total',
  'kpi.hitRate': 'Tasa de acierto',
  'kpi.hitRate.noBets': 'Aún no hay apuestas liquidadas',
  'kpi.hitRate.hint': 'Ganadas / apuestas liquidadas',
  'kpi.roi': 'ROI',
  'kpi.maxDrawdown': 'Drawdown máx.',
  'transparency.title': 'Tracker de transparencia',
  'transparency.updating':
    'Los datos de rendimiento se están actualizando.',
  'transparency.disclaimer':
    'Simulación hipotética de un modelo estadístico basado en datos históricos de partidos. No es una invitación a apostar. Sin garantía de resultados futuros. Apostar implica riesgos financieros.',
  'transparency.viewFullDetails': 'Ver todos los detalles',
  'recentBets.title': 'Apuestas recientes',
  'recentBets.captionFallback': 'Evaluación de value bets pasadas',
  'recentBets.captionTemplate':
    'Últimos {n} {dayLabel} · {bets} apuestas · Tasa de acierto {rate}',
  'recentBets.day.bet': 'Apuesta',
  'recentBets.day.bets': 'Apuestas',
  'recentBets.day.day': 'día',
  'recentBets.day.days': 'días',
  'recentBets.day.pending': '{n} pendientes',
  'recentBets.status.won': 'Ganada',
  'recentBets.status.lost': 'Perdida',
  'recentBets.status.pending': 'Pendiente',
  'recentBets.empty.title': 'Aún no hay apuestas liquidadas',
  'recentBets.empty.hint':
    'En cuanto terminen los primeros partidos, los resultados aparecerán aquí con valoración verde/roja.',
  'recentBets.updating': 'El historial se está actualizando.',
  'predictionCard.outcome.home': 'Victoria local',
  'predictionCard.outcome.draw': 'Empate',
  'predictionCard.outcome.away': 'Victoria visitante',
  'predictionCard.pick': 'Selección:',
  'predictionCard.vs': 'vs',
  'valueBet.confidence.high': 'Alta',
  'valueBet.confidence.medium': 'Media',
  'valueBet.confidence.low': 'Baja',
  'valueBet.odds': 'Cuota',
  'valueBet.edge': 'Edge',
  'valueBet.stake': 'Stake',
  'bankroll.empty':
    'Aún no hay datos de bankroll — registra apuestas para empezar el seguimiento.',
  'ratings.col.team': 'Equipo',
  'ratings.col.home': 'Local',
  'ratings.col.away': 'Visitante',
  'ratings.col.overall': 'Global',
  'ratings.col.form': 'Forma',
  'nav.today': 'Hoy',
  'nav.performance': 'Rendimiento',
  'nav.leagues': 'Ligas',
  'nav.language': 'Idioma',
  'footer.text':
    'Betting with AI · Ensamble CatBoost + Poisson + MLP · Modelo v0.3',
  'cookie.title': 'Usamos cookies',
  'cookie.body':
    'Este sitio utiliza cookies y tecnologías similares para garantizar su funcionamiento y para medir el alcance y el rendimiento. Tu consentimiento se almacena junto con un hash de tu dirección IP para poder reconocerlo en tu próxima visita. Puedes retirarlo en cualquier momento.',
  'cookie.necessary.title': 'Necesarias',
  'cookie.necessary.desc':
    'Imprescindibles para el funcionamiento del sitio. Siempre activas.',
  'cookie.analytics.title': 'Estadísticas',
  'cookie.analytics.desc': 'Medición anónima de uso para mejorar el sitio.',
  'cookie.marketing.title': 'Marketing',
  'cookie.marketing.desc': 'Contenido personalizado y seguimiento de terceros.',
  'cookie.btn.settings': 'Ajustes',
  'cookie.btn.hideDetails': 'Ocultar detalles',
  'cookie.btn.reject': 'Rechazar',
  'cookie.btn.save': 'Guardar selección',
  'cookie.btn.acceptAll': 'Aceptar todo',
  'cookie.aria.dialog': 'Consentimiento de cookies',
};
