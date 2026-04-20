import type { Dictionary } from './en';

export const fr: Dictionary = {
  'site.title': 'Betting with AI',
  'site.tagline':
    "Analyses de paris sportifs dopées à l'IA pour les cinq grands championnats de football.",
  'site.description':
    "Prédictions football et value bets basés sur les données pour la Premier League, la Bundesliga, la Serie A, la Liga et l'EFL Championship. Ensemble CatBoost + Poisson + MLP avec suivi de performance transparent.",
  'home.heading':
    "Analyses de paris du jour pour les cinq grands championnats.",
  'home.subheading':
    "Probabilités calibrées pour Victoire domicile, Match nul, Victoire extérieur — plus les value bets lorsque le modèle s'écarte du marché.",
  'home.loading': 'Chargement des prédictions…',
  'home.section.valueBets.title': 'Value Bets',
  'home.section.valueBets.caption':
    'Écarts détectés entre le modèle et le marché.',
  'home.section.valueBets.empty.title': 'Pas de value bets pour le moment',
  'home.section.valueBets.empty.hint':
    "Quand le modèle détecte un avantage significatif sur le marché, les opportunités s'afficheront ici.",
  'home.section.valueBets.info.aria': 'À propos du calcul de la mise',
  'home.section.valueBets.info.body':
    "La mise est dérivée du critère de Kelly : f* = (p · o − 1) / (o − 1), où p est notre probabilité de victoire calibrée et o la cote décimale. Nous appliquons un Kelly fractionné (¼) et plafonnons chaque pari à 5 % de la bankroll pour réduire la variance.",
  'home.section.predictions.title': 'Prédictions du jour',
  'home.section.predictions.caption':
    'Probabilités pour Domicile · Nul · Extérieur.',
  'home.section.predictions.empty.title': 'Aucune prédiction disponible',
  'home.section.predictions.empty.hint':
    'Génère un snapshot avec `fb snapshot` ou dépose un fichier de matchs dans « data/ ».',
  'home.stale.title': "Les prédictions du jour sont en cours de génération",
  'home.stale.hint':
    'Les cotes et les prédictions du modèle sont actualisées chaque matin. Merci de recharger dans quelques minutes.',
  'leagues.label': 'Championnats',
  'leagues.heading': 'Pi-Ratings et forme dans chaque grand championnat.',
  'leagues.description':
    "Pi-Ratings, forme récente et face-à-face pour la Premier League, la Bundesliga, la Serie A, la Liga et l'EFL Championship.",
  'leagues.teams': '{n} équipes',
  'leagues.leader': 'Leader :',
  'leagues.noData': 'Aucune donnée — exécute `fb download`.',
  'leagues.viewDetails': 'Voir les détails →',
  'league.back': '← Tous les championnats',
  'league.subtitle':
    'Pi-Ratings selon Constantinou & Fenton (2013) — séparés par force à domicile et à l’extérieur.',
  'league.section.table': 'Classement',
  'league.empty.title': 'Aucune donnée',
  'league.empty.hint':
    'Charge les données du championnat avec `fb download --league all`.',
  'performance.label': 'Transparence du modèle',
  'performance.heading': "Performance sur l'ensemble de l'historique de paris.",
  'performance.description':
    'Transparence totale sur le taux de réussite, le ROI, le drawdown maximal et la ventilation par championnat — mise à jour après chaque journée.',
  'performance.section.coreMetrics': 'Indicateurs clés',
  'performance.section.bankroll': 'Courbe de bankroll',
  'performance.section.bankroll.caption': 'Bankroll de départ : 1 000.',
  'performance.section.byLeague': 'Ventilation par championnat',
  'performance.byLeague.empty':
    'Aucun pari réglé par championnat pour le moment.',
  'performance.byLeague.col.league': 'Championnat',
  'performance.byLeague.col.name': 'Nom',
  'performance.byLeague.col.bets': 'Paris',
  'performance.byLeague.col.hitRate': 'Taux de réussite',
  'performance.byLeague.col.roi': 'ROI',
  'kpi.bets': 'Paris',
  'kpi.bets.hint': '{n} prédictions au total',
  'kpi.hitRate': 'Taux de réussite',
  'kpi.hitRate.noBets': 'Aucun pari réglé',
  'kpi.hitRate.hint': 'Gains / paris réglés',
  'kpi.roi': 'ROI',
  'kpi.maxDrawdown': 'Drawdown max.',
  'transparency.title': 'Suivi de transparence',
  'transparency.updating':
    'Les données de performance sont en cours de mise à jour.',
  'transparency.disclaimer':
    "Simulation hypothétique d'un modèle statistique basé sur des données historiques. Pas une incitation au jeu. Aucune garantie de résultats futurs. Le jeu comporte des risques financiers.",
  'transparency.viewFullDetails': 'Voir tous les détails',
  'recentBets.title': 'Paris récents',
  'recentBets.captionFallback': 'Évaluation des value bets passés',
  'recentBets.captionTemplate':
    '{n} derniers {dayLabel} · {bets} paris · Taux de réussite {rate}',
  'recentBets.day.bet': 'Pari',
  'recentBets.day.bets': 'Paris',
  'recentBets.day.day': 'jour',
  'recentBets.day.days': 'jours',
  'recentBets.day.pending': '{n} en attente',
  'recentBets.status.won': 'Gagné',
  'recentBets.status.lost': 'Perdu',
  'recentBets.status.pending': 'En attente',
  'recentBets.empty.title': 'Aucun pari réglé',
  'recentBets.empty.hint':
    "Dès que les premiers matchs seront terminés, les résultats apparaîtront ici avec une évaluation verte/rouge.",
  'recentBets.updating': "L'historique est en cours de mise à jour.",
  'recentBets.kind.value': 'Value',
  'recentBets.kind.prediction': 'Pronostic',
  'predictionCard.outcome.home': 'Victoire domicile',
  'predictionCard.outcome.draw': 'Match nul',
  'predictionCard.outcome.away': 'Victoire extérieur',
  'predictionCard.pick': 'Choix :',
  'predictionCard.badge.live': 'En direct',
  'predictionCard.badge.correct': 'Pronostic réussi',
  'predictionCard.badge.incorrect': 'Pronostic raté',
  'predictionCard.vs': 'vs',
  'valueBet.confidence.high': 'Élevée',
  'valueBet.confidence.medium': 'Moyenne',
  'valueBet.confidence.low': 'Faible',
  'valueBet.odds': 'Cote',
  'valueBet.edge': 'Edge',
  'valueBet.stake': 'Mise',
  'bankroll.empty':
    'Aucune donnée de bankroll — enregistre des paris pour commencer le suivi.',
  'ratings.col.team': 'Équipe',
  'ratings.col.home': 'Domicile',
  'ratings.col.away': 'Extérieur',
  'ratings.col.overall': 'Global',
  'ratings.col.form': 'Forme',
  'nav.today': "Aujourd'hui",
  'nav.performance': 'Performance',
  'nav.leagues': 'Championnats',
  'nav.language': 'Langue',
  'nav.about': 'À propos',
  'nav.methodology': 'Méthodologie',
  'footer.text':
    'Betting with AI · Ensemble CatBoost + Poisson + MLP · Modèle v0.3',
  'footer.col.product': 'Produit',
  'footer.col.about': 'À propos',
  'footer.col.legal': 'Mentions légales',
  'footer.col.responsible': 'Jeu responsable',
  'footer.link.today': "Pronostics du jour",
  'footer.link.leagues': 'Championnats',
  'footer.link.performance': 'Suivi de performance',
  'footer.link.about': 'À propos',
  'footer.link.methodology': 'Méthodologie',
  'footer.link.changelog': 'Changelog du modèle',
  'footer.link.sourceCode': 'Code source ↗',
  'footer.link.terms': "Conditions d'utilisation",
  'footer.link.privacy': 'Politique de confidentialité',
  'footer.link.cookies': 'Cookies',
  'footer.link.impressum': 'Mentions légales',
  'footer.link.responsibleGambling': 'Jeu responsable',
  'footer.link.helpline': 'Joueurs Info Service (FR)',
  'footer.disclaimer':
    "Contenu uniquement informatif. Pas de conseils de paris. Nous n'acceptons aucun enjeu et ne percevons aucune commission des bookmakers. Les performances passées du modèle ne garantissent pas les résultats futurs.",
  'footer.ageBadge.label': '18+ · Informations uniquement',
  'page.about.title': 'À propos de Betting with AI',
  'page.about.description':
    "Analytique football IA indépendante et sans partenariat, développée par un data scientist solo. Pourquoi nous existons, qui nous sommes et en quoi nous différons des sites de pronostics affiliés.",
  'page.methodology.title': 'Méthodologie · Comment notre modèle fonctionne',
  'page.methodology.description':
    'Pi-Ratings, CatBoost, Poisson Dixon-Coles, ensemble MLP, calibration isotonique et backtesting walk-forward — chaque composant expliqué en toute transparence.',
  'page.responsibleGambling.title': 'Jeu responsable',
  'page.responsibleGambling.description':
    "Aide, auto-exclusion et lignes d'écoute nationales en cas d'addiction au jeu en France, au Royaume-Uni, en Allemagne, en Italie et en Espagne.",
  'page.terms.title': "Conditions d'utilisation",
  'page.terms.description':
    "Conditions juridiques régissant l'utilisation de Betting with AI. Contenu purement éditorial — nous ne sommes pas un bookmaker et n'acceptons aucun pari.",
  'page.privacy.title': 'Politique de confidentialité',
  'page.privacy.description':
    'Comment Betting with AI traite les données personnelles, les cookies et les analytics selon le RGPD.',
  'page.cookies.title': 'Politique relative aux cookies',
  'page.cookies.description':
    'Quels cookies nous déposons, pourquoi, et comment gérer vos préférences.',
  'page.impressum.title': 'Mentions légales',
  'page.impressum.description':
    "Informations légales sur l'éditeur du site Betting with AI.",
  'page.trackRecord.title': 'Historique · Précision vérifiée',
  'page.trackRecord.description':
    "Historique public et téléchargeable de chaque pronostic Betting with AI face au résultat réel, avec graphique de calibration et téléchargement CSV. Sans cherry-picking.",
  'page.learn.title': 'Apprendre · Concepts des paris sportifs',
  'page.learn.description':
    "Guides clairs sur les value bets, les xG, le critère de Kelly, la calibration des modèles et plus encore — par un analyste IA indépendant du football.",
  'trackRecord.calibration.title': 'Graphique de calibration',
  'trackRecord.calibration.caption':
    'Probabilité prédite vs fréquence observée sur tous les résultats joués. La diagonale correspond à une calibration parfaite.',
  'trackRecord.csv.title': 'Télécharger le jeu de données complet',
  'trackRecord.csv.caption':
    'Chaque pronostic, avec les probabilités du modèle, le résultat réel et un indicateur de justesse. CSV, UTF-8.',
  'trackRecord.csv.button': 'Télécharger track-record.csv',
  'trackRecord.stats.records': 'Pronostics enregistrés',
  'trackRecord.stats.settled': 'Joués (avec résultat)',
  'learn.heading': 'Concepts des paris sportifs, expliqués clairement.',
  'learn.intro':
    "Guides courts et fondés sur des données pour les value bets, la calibration des modèles, la gestion de bankroll et les métriques utilisées pour juger ce site.",
  'learn.readMore': 'Lire →',
  'leagueHub.next5.title': '5 prochains matchs',
  'leagueHub.next5.empty': 'Aucun match à venir dans le snapshot actuel.',
  'leagueHub.last5.title': '5 derniers résultats',
  'leagueHub.last5.empty': 'Aucun résultat récent disponible.',
  'leagueHub.pickCorrect': 'Pronostic correct',
  'leagueHub.pickIncorrect': 'Pronostic incorrect',
  'leagueHub.viewMatch': 'Voir la prédiction →',
  'match.lineups.title': 'Compositions & notes des joueurs',
  'match.lineups.attribution': 'Données de composition en direct par Sofascore',
  'match.lineups.consentPrompt':
    'Les compositions en direct avec les notes des joueurs Sofascore sont disponibles pour ce match.',
  'match.lineups.consentNote':
    'Charger le widget transmet des données à sofascore.com et place des cookies tiers.',
  'match.lineups.consentButton': 'Charger les compositions Sofascore',
  'cookie.title': 'Nous utilisons des cookies',
  'cookie.body':
    "Ce site utilise des cookies et des technologies similaires pour assurer son fonctionnement et mesurer l'audience et les performances. Votre consentement est enregistré avec un hachage de votre adresse IP afin que nous puissions le reconnaître lors de votre prochaine visite. Vous pouvez le retirer à tout moment.",
  'cookie.necessary.title': 'Nécessaires',
  'cookie.necessary.desc':
    'Indispensables au fonctionnement du site. Toujours actifs.',
  'cookie.analytics.title': 'Statistiques',
  'cookie.analytics.desc':
    "Mesure d'audience anonyme pour améliorer le site.",
  'cookie.marketing.title': 'Marketing',
  'cookie.marketing.desc': 'Contenus personnalisés et suivi par des tiers.',
  'cookie.btn.settings': 'Paramètres',
  'cookie.btn.hideDetails': 'Masquer les détails',
  'cookie.btn.reject': 'Refuser',
  'cookie.btn.save': 'Enregistrer la sélection',
  'cookie.btn.acceptAll': 'Tout accepter',
  'cookie.aria.dialog': 'Consentement aux cookies',
};
