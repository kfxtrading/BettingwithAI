import type { LearnArticle } from './types';

const LAST_UPDATED = '2026-04-01';

const articles: Record<string, LearnArticle> = {
  'value-bets': {
    slug: 'value-bets',
    title: "Value Bets au football : définition et comment les trouver",
    description:
      "Une value bet est un pari dont la probabilité réelle de gagner est supérieure à la probabilité implicite du bookmaker. Découvrez comment les identifier — avec des exemples.",
    tldr:
      "Une value bet existe quand votre probabilité estimée est supérieure à la probabilité de marché sans marge du bookmaker. L'espérance de gain est positive, même si un pari individuel est perdu.",
    sections: [
      {
        heading: "Définition",
        paragraphs: [
          "Une value bet est tout pari pour lequel (votre probabilité estimée) × (cote décimale) > 1. Ce produit s'appelle l'espérance de gain (EG). Seule une espérance positive compte sur le long terme — le résultat d'un match individuel n'est que du bruit.",
          "La probabilité implicite du marché est 1 / cote, mais les cotes 1X2 brutes intègrent 4 à 8 % de marge bookmaker. Vous devez d'abord supprimer cette marge pour comparer équitablement.",
        ],
      },
      {
        heading: "Comment trouver des value bets",
        paragraphs: [
          "Utilisez un modèle avec des probabilités calibrées pour Domicile, Nul et Extérieur. Convertissez les trois cotes en probabilités implicites, normalisez-les pour qu'elles somment à 1, et comparez avec le modèle. Là où le modèle est supérieur d'au moins 2 à 3 points de pourcentage, il y a un potentiel de value.",
          "La taille de la mise est aussi importante que la détection d'un avantage. Le Kelly fractionné (typiquement 25 à 50 % du Kelly plein) maximise la croissance à long terme sans vous ruiner lors d'une mauvaise semaine.",
        ],
      },
      {
        heading: "Pourquoi la plupart des « pronostics » ne sont pas des value bets",
        paragraphs: [
          "Les sites de pronostics guidés par l'affiliation choisissent le résultat le plus probable, pas celui dont le prix est le plus erroné. Miser sur les favoris n'a rien à voir avec la value — un favori à 1,20 avec 90 % de vraie probabilité a une EG de 1,08 ; un outsider à 4,50 avec 25 % de vraie probabilité a une EG de 1,125. L'outsider est la value bet.",
        ],
      },
    ],
    faqs: [
      {
        question: "Les value bets sont-elles une garantie de gains ?",
        answer:
          "Non. Les value bets sont positives en espérance, pas sur chaque match individuel. Sur 100 paris, la variance peut être considérable ; elle ne devient véritablement mesurable qu'au-delà de plusieurs centaines de paris.",
      },
      {
        question: "Quelle doit être la taille minimale de l'avantage ?",
        answer:
          "La plupart des professionnels exigent ≥ 3 à 5 % d'avantage après prise en compte de l'incertitude du modèle et de la marge bookmaker, afin de compenser la variance et les coûts d'exécution.",
      },
      {
        question: "Pourquoi le bookmaker propose-t-il des value bets ?",
        answer:
          "Les bookmakers fixent leurs cotes pour le client médian. Les soft books réagissent lentement aux blessures, compositions et argent avisé — ce délai est la source de la value.",
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-01',
  },

  'implied-probability': {
    slug: 'implied-probability',
    title: "Probabilité implicite à partir des cotes : formule et déduction de la marge",
    description:
      "Convertissez les cotes décimales, fractionnaires et américaines en probabilités implicites — et apprenez à supprimer la marge bookmaker pour que les trois issues somment à 100 %.",
    tldr:
      "Probabilité implicite = 1 / cote décimale. Comme les trois probabilités 1X2 dépassent 100 % en somme (overround), vous devez diviser chacune par le total pour obtenir la probabilité sans marge.",
    sections: [
      {
        heading: "La formule",
        paragraphs: [
          "Pour les cotes décimales : implicite = 1 / cote. Une cote de 2,00 correspond à 50 %, une cote de 4,00 à 25 %.",
          "Pour les cotes fractionnaires (ex. 5/2) : implicite = dénominateur / (numérateur + dénominateur) = 2/7 ≈ 28,6 %.",
          "Pour les cotes américaines : positives (+150) → 100 / (150+100) = 40 % ; négatives (-200) → 200 / (200+100) = 66,7 %.",
        ],
      },
      {
        heading: "Déduction de la marge",
        paragraphs: [
          "Additionnez les trois probabilités implicites 1X2. Si la somme est 1,06, l'overround est de 6 %. Divisez chaque probabilité implicite par 1,06 — c'est l'estimation « vraie » du bookmaker que vous comparez à votre modèle.",
          "Pour les marchés à deux issues comme Plus/Moins, la même logique s'applique — divisez par la somme des deux probabilités implicites.",
        ],
      },
    ],
    faqs: [
      {
        question: "La marge est-elle toujours répartie uniformément ?",
        answer:
          "Non. Les bookmakers appliquent plus de marge sur les favoris ou les outsiders selon le biais de leur clientèle. La déduction proportionnelle est une approximation ; les méthodes Shin et Power sont plus précises.",
      },
      {
        question: "Pourquoi ma probabilité sans marge semble-t-elle trop faible ?",
        answer:
          "Parce que les cotes brutes surestiment toujours la conviction du bookmaker de la valeur de la marge. La déduction de la marge révèle la véritable appréciation du marché.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'kelly-criterion': {
    slug: 'kelly-criterion',
    title: "Critère de Kelly pour les paris sportifs : formule, exemples, limites",
    description:
      "Le critère de Kelly dimensionne chaque pari de façon à maximiser la croissance géométrique à long terme. Voici la formule, un exemple football et les raisons d'utiliser le Kelly fractionné.",
    tldr:
      "Mise Kelly = (b·p − q) / b, où b = cote − 1, p votre probabilité de gagner et q = 1 − p. Les professionnels n'utilisent généralement qu'un quart ou la moitié pour contrôler la variance.",
    sections: [
      {
        heading: "Formule et exemple de calcul",
        paragraphs: [
          "Vous estimez que Manchester City bat Arsenal avec une probabilité de 0,55. Cote 2,10 (b = 1,10). Kelly = (1,10 × 0,55 − 0,45) / 1,10 = 0,155 / 1,10 ≈ 14,1 % de la bankroll.",
          "Le demi-Kelly mise 7 %, le quart-Kelly 3,5 %. Le Kelly plein n'est mathématiquement optimal que si vos probabilités sont exactes — ce qui n'est jamais le cas.",
        ],
      },
      {
        heading: "Pourquoi le Kelly fractionné",
        paragraphs: [
          "Le Kelly plein est brutalement volatil : même un estimateur non biaisé avec un bruit réaliste génère des drawdowns de 30 à 50 %. Le Kelly fractionné sacrifie un peu de rendement à long terme contre des drawdowns nettement réduits — généralement un bon compromis.",
          "Limitez chaque pari individuel à 1 à 3 % de la bankroll indépendamment de Kelly, et évitez complètement les paris à espérance négative.",
        ],
      },
    ],
    faqs: [
      {
        question: "Que faire si Kelly est nul ou négatif ?",
        answer:
          "Ne pariez pas. Une valeur Kelly négative signifie que le pari a une espérance négative aux cotes proposées.",
      },
      {
        question: "Kelly fonctionne-t-il avec les combinés ?",
        answer:
          "Techniquement oui, mais la variance des combinés est si élevée que les mises Kelly deviennent infimes. La plupart des quants évitent les combinés, sauf pour la couverture.",
      },
      {
        question: "Comment dimensionner plusieurs paris simultanés ?",
        answer:
          "Utilisez le Kelly simultané : résolvez une petite optimisation qui dimensionne tous les paris ensemble sous une contrainte de mise totale. Ou appliquez le Kelly individuel et limitez l'exposition totale à 25 à 30 % de la bankroll.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'bankroll-management': {
    slug: 'bankroll-management',
    title: "Gestion de la bankroll aux paris football : guide pratique",
    description:
      "La gestion de la bankroll est la discipline qui consiste à choisir les mises pour survivre assez longtemps à la variance et laisser votre avantage opérer. Voici les règles qui fonctionnent vraiment.",
    tldr:
      "Traitez votre bankroll comme un capital séparé et fixe. Risquez 0,5 à 2 % par pari, ne courez pas après les pertes, et révisez les mises mensuellement — pas après chaque victoire ou défaite.",
    sections: [
      {
        heading: "Les cinq règles",
        paragraphs: [
          "1. Ne misez que de l'argent dont vous pouvez vous permettre de perdre. Jamais le loyer, les économies ou de l'argent emprunté.",
          "2. Standard 1 % de la bankroll par pari ; Kelly fractionné seulement si vos probabilités sont calibrées.",
          "3. Enregistrez chaque pari (date, marché, cote, mise, résultat, probabilité du modèle). Sans journal, pas d'avantage.",
          "4. Redimensionnez mensuellement, pas quotidiennement. Augmenter les mises après une bonne semaine est le piège classique de la variance.",
          "5. Fixez un stop-loss (ex. −25 % de la bankroll déclenche une révision du modèle) et un stop-win (à +50 % sécurisez la moitié des gains).",
        ],
      },
    ],
    faqs: [
      {
        question: "Quelle doit être la taille d'une bankroll de départ ?",
        answer:
          "Un montant dont la perte n'affecte pas votre vie. De nombreux parieurs sérieux en loisir démarrent avec 100 fois leur mise habituelle.",
      },
      {
        question: "Dois-je retirer mes gains ?",
        answer:
          "Oui, régulièrement. Les gains réalisés ne reviennent jamais en arrière. Beaucoup de parieurs retirent automatiquement 50 % de chaque gain mensuel.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'closing-line-value': {
    slug: 'closing-line-value',
    title: "Closing Line Value (CLV) : meilleur indicateur de ROI à long terme",
    description:
      "Le CLV mesure à quel point les cotes que vous avez prises étaient meilleures par rapport aux cotes au coup d'envoi. C'est le meilleur indicateur avancé de rentabilité.",
    tldr:
      "Closing Line Value (CLV) = (votre_cote / cote_finale) − 1. Un CLV constamment positif est la preuve statistique d'un avantage — avant même que les résultats ne soient disponibles.",
    sections: [
      {
        heading: "Pourquoi le CLV est plus important que le ROI à court terme",
        paragraphs: [
          "Le ROI sur 50 paris est majoritairement du bruit. Le CLV converge beaucoup plus vite : 200 paris suffisent souvent pour confirmer qu'un CLV moyen de +2 % est réel, tandis que 200 paris ne prouvent presque rien pour le ROI.",
          "Les sharps et les modélisateurs sont évalués sur le CLV lors des 6 à 12 premiers mois. Si le CLV est positif, la bankroll suit.",
        ],
      },
      {
        heading: "Comment mesurer",
        paragraphs: [
          "Enregistrez les cotes finales 1X2 (Pinnacle est la référence) et comparez avec vos cotes prises. Votre CLV est positif si vos cotes étaient plus élevées.",
          "Calculez la moyenne du CLV par pari. Un CLV moyen de +1,5 % après marge bookmaker signale déjà une stratégie profitable sur les books sharp.",
        ],
      },
    ],
    faqs: [
      {
        question: "Où trouver des cotes finales fiables ?",
        answer:
          "Pinnacle est le marché de référence de facto. Les archives publiques comme oddsportal.com et les CSV football-data.co.uk contiennent des cotes finales sur des milliers de matchs passés.",
      },
      {
        question: "Un pari peut-il avoir un CLV positif et quand même perdre ?",
        answer:
          "Bien sûr — le CLV mesure la compétence de tarification, pas la chance. Sur des centaines de paris, un CLV positif se traduit en ROI positif ; sur un match individuel, le résultat est du bruit.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'expected-goals-xg': {
    slug: 'expected-goals-xg',
    title: "Expected Goals (xG) expliqué : fonctionnement et pouvoir prédictif",
    description:
      "L'Expected Goals (xG) attribue à chaque tir une probabilité de but — basée sur la position, le type et le contexte. Ce que xG mesure, ce qu'il ne mesure pas, et comment l'utiliser pour les paris.",
    tldr:
      "Le xG est la somme des probabilités de but par tir. Sur une saison, le xG d'équipe est bien plus prédictif des résultats futurs que les buts marqués — la variance domine les petits échantillons.",
    sections: [
      {
        heading: "Quelles variables utilise un modèle xG",
        paragraphs: [
          "Chaque tir est évalué selon des caractéristiques telles que la distance au but, l'angle, la partie du corps, le type de passe (passe en profondeur vs centre), la pression défensive et le score. Le modèle fournit une probabilité entre 0 et 1 par tir.",
          "Le xG d'une équipe par match est la somme de ces probabilités. Sur 38 matchs, une équipe de Premier League avec +0,5 xG/match au-dessus de la moyenne de la ligue est presque assurée de figurer dans le top six.",
        ],
      },
      {
        heading: "Comment utiliser le xG dans la prévision de matchs",
        paragraphs: [
          "Le xG-for et xG-against glissants sur 5 à 10 matchs sont de meilleures variables que la différence de buts brute, car ils éliminent la variance des finisseurs et les séries chaudes des gardiens.",
          "Combinez le xG avec la qualité des tirs (xG par tir) pour identifier les équipes qui créent des occasions différemment — les équipes à haute qualité d'occasion sont plus durables que celles à haute quantité d'occasion.",
        ],
      },
    ],
    faqs: [
      {
        question: "Le xG est-il meilleur que les buts ?",
        answer:
          "Pour prédire les matchs futurs, presque toujours oui. Pour décrire ce qui s'est passé, les buts l'emportent — seuls eux comptent au classement.",
      },
      {
        question: "Pourquoi les modèles xG se contredisent-ils ?",
        answer:
          "Différents fournisseurs utilisent des variables et des données d'entraînement différentes. Utilisez un modèle de manière cohérente ; les comparaisons relatives importent plus que les valeurs absolues.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'btts-explained': {
    slug: 'btts-explained',
    title: "Les deux équipes marquent (BTTS) : stratégie, cotes et erreurs fréquentes",
    description:
      "Le BTTS paie quand les deux équipes marquent au moins un but. Comment le marché fixe les prix, quand il se trompe et ce qu'il faut surveiller dans les profils d'équipe.",
    tldr:
      "BTTS Oui est profitable quand deux équipes offensives avec des défenses fragiles s'affrontent — cotes typiques 1,65 à 1,90. Le xG brut est un fort prédicteur ; la variance pure des tirs ne l'est pas.",
    sections: [
      {
        heading: "Quand BTTS Oui a de la value",
        paragraphs: [
          "Cherchez des équipes qui génèrent chacune ≥ 1,3 xG-for et ≥ 1,0 xG-against par match sur les 10 dernières rencontres. Les équipes mi-tableau offensives livrent historiquement bien sur le BTTS.",
          "Évitez BTTS Oui lors de matchs avec des défenses d'élite et de forts gardiens — ils produisent trop de résultats « clean sheet ».",
        ],
      },
      {
        heading: "BTTS Non : le jeu contrarian",
        paragraphs: [
          "BTTS Non est sous-évalué quand un favori clair affronte un outsider défensivement faible : le favori gagne souvent sans encaisser. Les moyennes de ligue aident : la Serie A a historiquement des taux BTTS Non plus élevés que la Bundesliga.",
        ],
      },
    ],
    faqs: [
      {
        question: "Que signifie « BTTS Oui & Plus de 2,5 » ?",
        answer:
          "Un marché combiné : les deux équipes doivent marquer ET le nombre de buts doit être ≥ 3. Plus exigeant, avec des cotes plus longues.",
      },
      {
        question: "Le BTTS est-il plus facile à prédire que le 1X2 ?",
        answer:
          "C'est un résultat binaire, donc plus simple à calibrer. Mais la marge sur le BTTS est souvent plus élevée que sur le 1X2 — l'avantage par pari est généralement plus faible.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'over-under-2-5': {
    slug: 'over-under-2-5',
    title: "Plus/Moins de 2,5 buts : comment fonctionne le marché et comment le battre",
    description:
      "Plus de 2,5 paie à partir de 3 buts. Comment prédire les totaux de buts via le xG, le contexte de ligue et les signaux de tempo.",
    tldr:
      "Plus/Moins de 2,5 est réglé au seuil de 3 buts. Prédisez à partir du xG-for combiné + xG-against adverse, de la moyenne de ligue et des effets domicile/extérieur.",
    sections: [
      {
        heading: "Modélisation du total de buts",
        paragraphs: [
          "Un modèle Poisson simple utilise les buts attendus des deux équipes + les buts encaissés adverses, ajustés à la moyenne de ligue. Des buts attendus combinés ≥ 2,7 soutiennent un penchant Plus-2,5 à des cotes équitables.",
          "Dixon-Coles affine Poisson en corrigeant les corrélations des faibles scores (0-0, 1-0, 0-1, 1-1) — standard en modélisation football depuis 1997.",
        ],
      },
      {
        heading: "Erreurs fréquentes",
        paragraphs: [
          "Le biais de récence est le tueur. Un 4-0 au dernier match pousse les parieurs occasionnels vers Plus ; le modèle devrait à peine bouger, car les buts attendus changent peu.",
          "Ignorer la météo et les conditions de terrain en hiver — un terrain lourd ou un vent fort réduisent fiablement le seuil de buts.",
        ],
      },
    ],
    faqs: [
      {
        question: "Quel est le taux de Plus de 2,5 sur le long terme ?",
        answer:
          "Sur les cinq grands championnats, il est d'environ 53 à 55 %. À une cote typique de 1,85, le seuil de rentabilité est 54,1 % — un marché serré.",
      },
      {
        question: "Qu'est-ce que l'Asian Handicap sur Plus de 2,5 ?",
        answer:
          "Les marchés Asian Total décalent la ligne de 0,25 ou 0,5 pour éviter les résultats nuls. Plus de 2,75 divise la mise entre Plus de 2,5 et Plus de 3,0.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  '1x2-explained': {
    slug: '1x2-explained',
    title: "Le pari 1X2 expliqué : le marché football le plus liquide",
    description:
      "Le 1X2 est un pari à trois issues sur la victoire à domicile (1), le nul (X) ou la victoire à l'extérieur (2). Comment il est coté, pourquoi les marges varient et où se trouve la value.",
    tldr:
      "Le 1X2 est le marché football le plus profond et le plus liquide. Les trois probabilités implicites somment à 104 à 108 % — l'overround. Après déduction de la marge, on obtient la vraie appréciation du marché.",
    sections: [
      {
        heading: "Comment le marché fixe les prix",
        paragraphs: [
          "Les books sharp comme Pinnacle cotent le 1X2 avec 100,5 à 101 % (marge inférieure à 2 %). Les books récréatifs appliquent 5 à 8 % de marge. Comparez toujours plusieurs books avant de parier.",
          "Le nul est systématiquement plus difficile à prédire que les victoires — la probabilité implicite du nul se situe typiquement dans une fourchette étroite de 22 à 28 %, c'est pourquoi la plupart des avantages se trouvent côté domicile ou extérieur.",
        ],
      },
      {
        heading: "Où vit la value 1X2",
        paragraphs: [
          "Les surréactions du marché aux résultats récents (victoires 4-0, défaites en derby) sur de petits échantillons. Les modèles ignorant le bruit à court terme battent constamment les lignes fixées manuellement ici.",
          "Les matchs en fin de saison sans enjeu sportif — l'argent public sur-récompense l'équipe encore motivée.",
        ],
      },
    ],
    faqs: [
      {
        question: "Qu'est-ce que « 1N2 » sur les sites français ?",
        answer:
          "Identique au 1X2 : 1 = victoire à domicile, N = Nul, 2 = victoire à l'extérieur. Seulement la notation, pas de différence.",
      },
      {
        question: "Dois-je parier sur le nul ?",
        answer:
          "Seulement si votre probabilité calibrée est supérieure à la probabilité implicite. Dans les matchs serrés, le nul est presque pile ou face ; beaucoup de modèles s'abstiennent simplement.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'model-accuracy-brier-calibration': {
    slug: 'model-accuracy-brier-calibration',
    title: "Comment évaluer les modèles de prévision football : Brier, RPS et calibration",
    description:
      "Le taux de réussite est une mauvaise métrique pour les modèles probabilistes. Le Brier Score, le RPS et les diagrammes de fiabilité montrent si un modèle est vraiment calibré.",
    tldr:
      "Utilisez le Brier Score et le Ranked Probability Score (RPS) pour comparer, ainsi qu'un diagramme de fiabilité pour vérifier si les pronostics à « 70 % » gagnent réellement dans 70 % des cas.",
    sections: [
      {
        heading: "Pourquoi le taux de réussite est trompeur",
        paragraphs: [
          "Un modèle qui choisit toujours le favori atteint ~52 % de taux de réussite en Premier League — mais n'offre aucun avantage sur le bookmaker. Le taux de réussite ne vérifie que l'argmax, pas les probabilités.",
        ],
      },
      {
        heading: "Brier Score et RPS",
        paragraphs: [
          "Brier = erreur quadratique moyenne entre le vecteur de probabilités et le résultat one-hot. Plus bas est mieux.",
          "Le RPS (Ranked Probability Score) est le cousin ordinal du Brier : il pénalise davantage les erreurs confiantes sur les issues adjacentes — la référence de facto pour le 1X2.",
        ],
      },
      {
        heading: "Diagrammes de fiabilité",
        paragraphs: [
          "Regroupez toutes les probabilités prédites en 10 bins. Tracez la probabilité prédite moyenne par bin face au taux de réussite réel. Un modèle parfaitement calibré se situe sur la diagonale.",
          "Nous publions le diagramme de fiabilité des prévisions en direct sous /track-record.",
        ],
      },
    ],
    faqs: [
      {
        question: "Quelle est une bonne plage RPS pour le 1X2 au football ?",
        answer:
          "Les cinq grands championnats se situent entre 0,19 et 0,21 pour les modèles bien calibrés. En dessous de 0,20 est très fort ; au-dessus de 0,22 indique des problèmes de calibration.",
      },
      {
        question: "Pourquoi ne pas simplement utiliser le Log-Loss ?",
        answer:
          "Le Log-Loss pénalise infiniment les erreurs confiantes. Le Brier est plus robuste face aux coups chanceux rares ; le RPS respecte la structure ordinale de D/N/E.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },
};

export default articles;
