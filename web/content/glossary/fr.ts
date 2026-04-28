import type { GlossaryEntry } from './en';

const LAST_UPDATED = '2026-04-28';

const entries: readonly GlossaryEntry[] = [
  {
    slug: 'value-bet',
    term: 'Value bet',
    shortDefinition:
      'Un pari dont la probabilité réelle de gain dépasse la probabilité implicite du bookmaker, donnant une valeur attendue positive.',
    body:
      'Une value bet est tout pari où la probabilité estimée du résultat, multipliée par la cote décimale, est supérieure à 1. Le produit est la valeur attendue (VA), et une value bet est par définition tout pari avec VA au-dessus de 1,0. La probabilité implicite du marché est 1 / cote_décimale, mais les cotes 1N2 brutes incluent une marge de 4 à 8 % du bookmaker ; pour comparer honnêtement, les trois probabilités implicites doivent être normalisées pour totaliser 1,0. Le value betting est la seule stratégie rentable à long terme dans les paris sportifs car elle est indépendante du fait que le favori ou l\'outsider gagne. Des résultats à court terme sont bruités ; les value bets ne deviennent rentables que sur des centaines de paris avec une mise disciplinée.',
    related: ['expected-value', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'expected-value',
    term: 'Valeur attendue (VA)',
    shortDefinition:
      'Le profit ou la perte moyen d\'un pari par unité misée, calculé comme probabilité × cote moins un.',
    termCode: 'VA',
    body:
      'La valeur attendue (VA) est le résultat moyen à long terme d\'un pari répété, exprimé par unité misée. Pour un pari à cotes décimales, la formule est VA = p × cote − 1, où p est la vraie probabilité de gagner. Une VA positive signifie que, répété suffisamment de fois avec une gestion appropriée de la bankroll, le pari sera rentable en moyenne. La VA est le concept le plus important dans les paris sportifs car elle sépare la compétence de la chance : les courtes séries de résultats sont dominées par la variance, mais la VA détermine la direction du long terme. Un pari peut perdre neuf fois sur dix et avoir quand même été la bonne décision si sa VA était positive.',
    related: ['value-bet', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'implied-probability',
    term: 'Probabilité implicite',
    shortDefinition:
      'La probabilité intégrée dans la cote d\'un bookmaker, égale à 1 / cote_décimale avant suppression de la marge.',
    body:
      'La probabilité implicite est la probabilité que les cotes décimales d\'un bookmaker suggèrent pour un résultat, calculée comme 1 / cote_décimale. Les probabilités implicites 1N2 brutes s\'additionnent à plus de 100 % — généralement 104 à 108 % — car les bookmakers intègrent une marge, également appelée surround ou vig. Pour comparer équitablement la probabilité du marché avec un modèle, les trois probabilités implicites brutes doivent être normalisées en divisant chacune par leur somme, de sorte qu\'elles totalisent exactement 1,0. Seules les probabilités implicites normalisées représentent la vision honnête du bookmaker. La différence entre les chiffres bruts et normalisés du bookmaker est exactement l\'avantage de la maison sur ce marché.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'kelly-criterion',
    term: 'Critère de Kelly',
    shortDefinition:
      'Une formule de taille de mise qui maximise la croissance géométrique à long terme d\'une bankroll en présence d\'un avantage connu.',
    termCode: 'Kelly',
    body:
      'Le critère de Kelly est une formule de mise développée par John Kelly en 1956 qui maximise le taux de croissance géométrique d\'une bankroll. Pour un pari à cotes décimales, la formule est f = (p × cote − 1) / (cote − 1), où p est la vraie probabilité de gagner et f la fraction de bankroll à miser. Le Kelly complet n\'est optimal que lorsque les probabilités sont connues exactement ; en pratique, l\'incertitude du modèle signifie que les mises Kelly complètes sont trop volatiles. La plupart des parieurs professionnels utilisent donc le Kelly fractionné — typiquement 25 à 50 % de la mise Kelly complète — qui préserve la majeure partie de la croissance à long terme tout en réduisant le risque de drawdown de moitié.',
    related: ['expected-value', 'value-bet', 'bankroll'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'pi-rating',
    term: 'Pi-rating',
    shortDefinition:
      'Un système de notation de force spécifique au football, successeur d\'Elo avec des ratings domicile et extérieur séparés par équipe.',
    body:
      'Les Pi-ratings sont un système de notation de force spécifique au football proposé par Constantinou et Fenton (2013) comme successeur d\'Elo. Chaque équipe a deux ratings numériques — domicile et extérieur — mis à jour après chaque match avec une fonction non linéaire de la différence de buts, plafonnée pour réduire l\'influence des grandes victoires. Les innovations clés par rapport à Elo sont la division explicite domicile/extérieur, qui capture avec précision les effets du terrain sans constante globale d\'avantage à domicile, et la mise à jour non linéaire de la différence de buts, qui converge plus rapidement après les promotions et relégations.',
    related: ['elo-rating', 'expected-goals'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'catboost',
    term: 'CatBoost',
    shortDefinition:
      'Une bibliothèque d\'arbres de décision à gradient boosting optimisée pour les features catégorielles et le boosting ordonné.',
    body:
      'CatBoost est une bibliothèque d\'arbres de décision à gradient boosting publiée par Yandex en 2017. Elle diffère de XGBoost et LightGBM sur deux points pratiquement importants : la gestion native des features catégorielles sans encodage one-hot, et le boosting ordonné, qui réduit le target leakage lors de l\'entraînement. Ces deux avantages comptent pour la prédiction football, où l\'identité de l\'équipe, l\'arbitre, le stade et le jour de la semaine sont des features catégorielles à haute cardinalité. Empiriquement, CatBoost surpasse XGBoost d\'environ 0,003 points de ranked probability score sur les prédictions 1N2 sans ajustement des hyperparamètres.',
    related: ['expected-value', 'calibration'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'calibration',
    term: 'Calibration probabiliste',
    shortDefinition:
      'La propriété selon laquelle les probabilités déclarées correspondent aux fréquences d\'occurrence observées sur de nombreuses prédictions.',
    body:
      'Une estimation de probabilité est bien calibrée lorsque la fraction de positifs parmi les prédictions avec la probabilité déclarée p est égale à p, sur de nombreux échantillons. Un modèle qui dit 70 % dix mille fois devrait avoir raison environ 7 000 fois. La calibration est une qualité distincte de la discrimination : un modèle peut trier correctement les gagnants des perdants et quand même citer de mauvaises probabilités absolues — et un tel modèle est inutile pour les paris car les calculs de valeur attendue nécessitent des probabilités correctes. L\'Expected Calibration Error (ECE) est la mesure scalaire la plus courante ; les modèles de paris en production visent un ECE inférieur à 1,5 %.',
    related: ['catboost', 'expected-value', 'brier-score'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'closing-line-value',
    term: 'Valeur de la cote de clôture (CLV)',
    shortDefinition:
      'La différence entre la cote à laquelle un pari a été placé et la cote de clôture au coup d\'envoi.',
    termCode: 'CLV',
    body:
      'La valeur de la cote de clôture (CLV) mesure si un parieur obtient un meilleur prix que celui que le marché établit au coup d\'envoi. Si vous pariez à 2,00 et que la cote de clôture est 1,90, vous avez un CLV positif ; le marché a évolué contre votre côté, ce qui est une forte indication que vous avez identifié un avantage avant que des parieurs plus avisés arrivent. Le CLV est largement considéré comme le meilleur indicateur avancé du profit de paris à long terme car les cotes de clôture sont le prix le plus efficace que le marché produit. Un CLV moyen positif sur un grand échantillon implique presque toujours un ROI attendu positif.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'btts',
    term: 'Les deux équipes marquent (BTTS)',
    shortDefinition:
      'Un marché football qui se règle Oui si les deux équipes marquent au moins un but et Non dans le cas contraire.',
    termCode: 'BTTS',
    body:
      'Les deux équipes marquent (BTTS) est un marché football binaire qui se règle Oui lorsque les deux équipes marquent au moins un but pendant le temps réglementaire et Non dans le cas contraire. Il est populaire car un seul but tardif peut convertir un ticket perdant. Du point de vue de la modélisation, le BTTS est dérivé de la distribution conjointe des buts domicile et extérieur : sous un modèle de Poisson bivarié de Dixon-Coles, P(BTTS=Oui) = 1 − P(BD=0) − P(BE=0) + P(BD=0, BE=0). Les taux de base BTTS au niveau de la ligue se situent généralement entre 48 et 58 %.',
    related: ['over-under-2-5', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'over-under-2-5',
    term: 'Plus/Moins de 2,5 buts',
    shortDefinition:
      'Un marché football qui se règle Plus si trois buts ou plus sont marqués et Moins si deux ou moins.',
    body:
      'Plus/Moins de 2,5 buts est le marché de buts football le plus échangé dans le monde. Il se règle Plus lorsque trois buts ou plus sont marqués en temps réglementaire et Moins lorsque deux ou moins sont marqués ; le demi-but évite les résultats nuls. Comme le BTTS, il est dérivé de la distribution conjointe des buts : avec un modèle de Poisson Dixon-Coles, on calcule P(Plus de 2,5) = 1 − P(total buts ≤ 2). Les taux de base des ligues varient d\'environ 47 % dans les ligues défensives à 58 % dans les ligues prolifiques comme la Bundesliga.',
    related: ['btts', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
];

export default entries;
