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
  'home.section.valueBets.info.aria': 'Sobre el cálculo de la apuesta',
  'home.section.valueBets.info.body':
    'La apuesta se deriva del criterio de Kelly: f* = (p · o − 1) / (o − 1), donde p es nuestra probabilidad de victoria calibrada y o la cuota decimal. Aplicamos un Kelly fraccionado (¼) y limitamos cada apuesta al 5 % del bankroll para reducir la varianza.',
  'home.section.predictions.title': 'Pronósticos de hoy',
  'home.section.predictions.caption':
    'Probabilidades para Local · Empate · Visitante.',
  'home.section.predictions.empty.title': 'Sin pronósticos disponibles',
  'home.section.predictions.empty.hint':
    'Genera un snapshot con `fb snapshot` o coloca un archivo de partidos en «data/».',
  'home.stale.title': 'Los pronósticos de hoy se están generando',
  'home.stale.hint':
    'Las cuotas y los pronósticos del modelo se actualizan cada mañana. Por favor, recarga en unos minutos.',
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
  'recentBets.kind.value': 'Value',
  'recentBets.kind.prediction': 'Pronóstico',
  'predictionCard.outcome.home': 'Victoria local',
  'predictionCard.outcome.draw': 'Empate',
  'predictionCard.outcome.away': 'Victoria visitante',
  'predictionCard.pick': 'Selección:',
  'predictionCard.badge.live': 'En vivo',
  'predictionCard.badge.correct': 'Pronóstico acertado',
  'predictionCard.badge.incorrect': 'Pronóstico fallado',
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
  'nav.about': 'Acerca de',
  'nav.methodology': 'Metodología',
  'footer.text':
    'Betting with AI · Ensamble CatBoost + Poisson + MLP · Modelo v0.3',
  'footer.col.product': 'Producto',
  'footer.col.about': 'Acerca de',
  'footer.col.legal': 'Aviso legal',
  'footer.col.responsible': 'Juego responsable',
  'footer.link.today': 'Pronósticos de hoy',
  'footer.link.leagues': 'Ligas',
  'footer.link.performance': 'Tracker de rendimiento',
  'footer.link.about': 'Acerca de',
  'footer.link.methodology': 'Metodología',
  'footer.link.changelog': 'Changelog del modelo',
  'footer.link.sourceCode': 'Código fuente ↗',
  'footer.link.terms': 'Términos del servicio',
  'footer.link.privacy': 'Política de privacidad',
  'footer.link.cookies': 'Cookies',
  'footer.link.impressum': 'Aviso legal',
  'footer.link.responsibleGambling': 'Juego responsable',
  'footer.link.helpline': 'FEJAR · Juego responsable (ES)',
  'footer.disclaimer':
    'Contenido solo informativo. No es asesoramiento de apuestas. No aceptamos apuestas ni recibimos comisiones de las casas de apuestas. El rendimiento pasado del modelo no garantiza resultados futuros.',
  'footer.ageBadge.label': '+18 · Solo informativo',
  'page.about.title': 'Acerca de Betting with AI',
  'page.about.description':
    'Analítica de fútbol IA independiente y sin afiliaciones, construida por un científico de datos en solitario. Por qué existimos, quiénes somos y en qué nos diferenciamos de los sitios de pronósticos afiliados.',
  'page.methodology.title': 'Metodología · Cómo funciona nuestro modelo',
  'page.methodology.description':
    'Pi-Ratings, CatBoost, Poisson Dixon-Coles, ensamble MLP, calibración isotónica y backtesting walk-forward — cada componente explicado con transparencia.',
  'page.responsibleGambling.title': 'Juego responsable',
  'page.responsibleGambling.description':
    'Ayuda, autoexclusión y líneas nacionales contra la ludopatía en España, Reino Unido, Alemania, Francia e Italia.',
  'page.terms.title': 'Términos del servicio',
  'page.terms.description':
    'Términos legales que rigen el uso de Betting with AI. Solo contenido editorial — no somos una casa de apuestas y no aceptamos apuestas.',
  'page.privacy.title': 'Política de privacidad',
  'page.privacy.description':
    'Cómo Betting with AI gestiona los datos personales, cookies y analítica conforme al RGPD.',
  'page.cookies.title': 'Política de cookies',
  'page.cookies.description':
    'Qué cookies utilizamos, por qué y cómo gestionar tus preferencias.',
  'page.impressum.title': 'Aviso legal',
  'page.impressum.description':
    'Información legal sobre el editor del sitio Betting with AI.',
  'page.trackRecord.title': 'Historial · Precisión verificada',
  'page.trackRecord.description':
    'Historial público y descargable de cada pronóstico de Betting with AI frente al resultado real, con gráfico de calibración y descarga en CSV. Sin cherry-picking.',
  'page.learn.title': 'Aprende · Conceptos de apuestas de fútbol',
  'page.learn.description':
    'Guías claras sobre value bets, goles esperados, criterio de Kelly, calibración del modelo y más — por un analista IA independiente de fútbol.',
  'trackRecord.calibration.title': 'Gráfico de calibración',
  'trackRecord.calibration.caption':
    'Probabilidad predicha vs frecuencia observada en todos los resultados finalizados. La diagonal es la calibración perfecta.',
  'trackRecord.csv.title': 'Descargar el dataset completo',
  'trackRecord.csv.caption':
    'Cada pronóstico, con probabilidades del modelo, resultado real e indicador de acierto. CSV, UTF-8.',
  'trackRecord.csv.button': 'Descargar track-record.csv',
  'trackRecord.stats.records': 'Pronósticos registrados',
  'trackRecord.stats.settled': 'Finalizados (con resultado)',
  'learn.heading': 'Conceptos de apuestas de fútbol, explicados con claridad.',
  'learn.intro':
    'Guías breves y basadas en datos sobre value bets, calibración del modelo, gestión del bankroll y las métricas con las que se evalúa este sitio.',
  'learn.readMore': 'Leer →',
  'leagueHub.next5.title': 'Próximos 5 partidos',
  'leagueHub.next5.empty': 'No hay partidos próximos en el snapshot actual.',
  'leagueHub.last5.title': 'Últimos 5 resultados',
  'leagueHub.last5.empty': 'Aún no hay resultados recientes disponibles.',
  'leagueHub.pickCorrect': 'Pronóstico acertado',
  'leagueHub.pickIncorrect': 'Pronóstico fallido',
  'leagueHub.viewMatch': 'Abrir predicción →',
  'match.lineups.title': 'Alineaciones y valoraciones de jugadores',
  'match.lineups.attribution': 'Datos de alineación en vivo de Sofascore',
  'match.lineups.consentPrompt':
    'Las alineaciones en vivo con las valoraciones de jugadores de Sofascore están disponibles para este partido.',
  'match.lineups.consentNote':
    'Cargar el widget transmite datos a sofascore.com y establece cookies de terceros.',
  'match.lineups.consentButton': 'Cargar alineaciones de Sofascore',
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
  'support.toggle.label': 'Ayuda / Soporte',
  'support.panel.title': 'Chat de soporte',
  'support.panel.close': 'Cerrar chat de soporte',
  'support.input.placeholder': 'Haz una pregunta…',
  'support.input.send': 'Enviar',
  'support.suggestions.heading': 'Preguntas frecuentes',
  'support.fallback':
    'Lo siento, no he encontrado una respuesta exacta. Reformula la pregunta o utiliza los datos de contacto del pie de página.',
  'support.faq.valueBet.q': '¿Qué es una value bet?',
  'support.faq.valueBet.a':
    'Una value bet es una apuesta en la que nuestro modelo estima una probabilidad real de victoria mayor que la implícita en las cuotas del operador. Esa diferencia (edge) hace que la apuesta sea +EV a largo plazo.',
  'support.faq.accuracy.q': '¿Qué precisión tienen las predicciones?',
  'support.faq.accuracy.a':
    'Usamos un ensemble de CatBoost + Poisson Dixon-Coles + un MLP, calibrado con regresión isotónica. El RPS típico por liga oscila entre 0,18 y 0,21. Consulta la página Track Record para un registro verificado.',
  'support.faq.dataSource.q': '¿De dónde proceden los datos?',
  'support.faq.dataSource.a':
    'Los resultados y las cuotas de cierre provienen de los feeds CSV de Football-Data.co.uk para las 5 grandes ligas. Los datos opcionales de alineaciones y xG se obtienen de Sofascore (solo con consentimiento).',
  'support.faq.snapshotUpdate.q': '¿Con qué frecuencia se actualizan las predicciones?',
  'support.faq.snapshotUpdate.a':
    'Cada mañana se genera un nuevo snapshot. En jornadas en vivo, la lista de value bets se refresca cada 45–60 segundos a medida que se mueven las cuotas.',
  'support.faq.kelly.q': '¿Cómo se calcula el stake recomendado?',
  'support.faq.kelly.a':
    'Aplicamos un criterio Kelly fraccionado (¼ Kelly) con un tope del 5 % del bankroll por apuesta: f* = (p · o − 1) / (o − 1), donde p es nuestra probabilidad calibrada y o la cuota decimal. Reduce la varianza respecto al Kelly completo.',
  'support.faq.piRating.q': '¿Qué es un Pi-Rating?',
  'support.faq.piRating.a':
    'Los Pi-Ratings (Constantinou & Fenton, 2013) dividen cada equipo en fuerza en casa y fuera, y se actualizan tras cada partido con la diferencia entre la diferencia de goles prevista y la real. Alimentan directamente nuestro modelo Poisson.',
  'support.faq.responsible.q': '¿Esto es asesoramiento financiero o de apuestas?',
  'support.faq.responsible.a':
    'No. Betting with AI es puramente informativo y no constituye una invitación a apostar. No aceptamos apuestas. Juega con responsabilidad — consulta la página de Juego Responsable para líneas de ayuda y autoexclusión.',
  'support.faq.language.q': '¿Cómo cambio el idioma?',
  'support.faq.language.a':
    'Usa el selector de idioma en la barra de navegación superior. Actualmente soportamos inglés, alemán, español, francés e italiano.',
  'support.faq.cookies.q': '¿Cómo cambio mis preferencias de cookies?',
  'support.faq.cookies.a':
    'Abre el pie de página y haz clic en "Cookies" — allí puedes reabrir el diálogo de consentimiento en cualquier momento y ajustar las cookies de análisis o marketing.',
  'support.faq.contact.q': '¿Cómo contacto con el equipo?',
  'support.faq.contact.a':
    'Los datos de contacto están en el Impressum (pie de página). Para problemas técnicos, abre un issue en el repositorio público de código fuente enlazado en el pie de página.',
};
