import type { GlossaryEntry } from './en';

const LAST_UPDATED = '2026-04-28';

const entries: readonly GlossaryEntry[] = [
  {
    slug: 'value-bet',
    term: 'Value bet',
    shortDefinition:
      'Una apuesta cuya verdadera probabilidad de ganar supera la probabilidad implícita del bookmaker, dando un valor esperado positivo.',
    body:
      'Una value bet es cualquier apuesta donde la probabilidad estimada del resultado, multiplicada por la cuota decimal, es mayor que 1. El producto es el valor esperado (VE), y una value bet es por definición cualquier apuesta con VE superior a 1,0. La probabilidad implícita del mercado es 1 / cuota_decimal, pero las cuotas 1X2 brutas incluyen un margen del 4–8% del bookmaker; para comparar honestamente, las tres probabilidades implícitas deben normalizarse para sumar 1,0. El value betting es la única estrategia rentable a largo plazo en las apuestas deportivas porque es agnóstica respecto a si gana el favorito o el outsider. Los resultados a corto plazo son ruidosos; las value bets solo se vuelven rentables a lo largo de cientos de apuestas con una apuesta disciplinada.',
    related: ['expected-value', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'expected-value',
    term: 'Valor esperado (VE)',
    shortDefinition:
      'El beneficio o pérdida promedio de una apuesta por unidad apostada, calculado como probabilidad × cuota menos uno.',
    termCode: 'VE',
    body:
      'El valor esperado (VE) es el resultado promedio a largo plazo de una apuesta repetida, expresado por unidad apostada. Para una apuesta a cuotas decimales la fórmula es VE = p × cuota − 1, donde p es la verdadera probabilidad de ganar. Un VE positivo significa que, repetida suficientes veces con una gestión adecuada del bankroll, la apuesta será rentable en promedio. El VE es el concepto más importante en las apuestas deportivas porque separa la habilidad de la suerte: las cortas secuencias de resultados están dominadas por la varianza, pero el VE determina la dirección del largo plazo. Una apuesta puede perder nueve de cada diez veces y haber sido igualmente la decisión correcta si su VE era positivo.',
    related: ['value-bet', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'implied-probability',
    term: 'Probabilidad implícita',
    shortDefinition:
      'La probabilidad incorporada en la cuota de un bookmaker, igual a 1 / cuota_decimal antes de eliminar el margen.',
    body:
      'La probabilidad implícita es la probabilidad que las cuotas decimales de un bookmaker sugieren para un resultado, calculada como 1 / cuota_decimal. Las probabilidades implícitas 1X2 brutas suman más del 100% — típicamente 104–108% — porque los bookmakers incluyen un margen, también llamado overround o vig. Para comparar la probabilidad del mercado con un modelo de forma justa, las tres probabilidades implícitas brutas deben normalizarse dividiéndolas por su suma, de modo que totalicen exactamente 1,0. Solo las probabilidades implícitas normalizadas representan la visión honesta del bookmaker. La diferencia entre las cifras brutas y normalizadas del bookmaker es exactamente la ventaja de la casa en ese mercado.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'kelly-criterion',
    term: 'Criterio de Kelly',
    shortDefinition:
      'Una fórmula para el tamaño de la apuesta que maximiza el crecimiento geométrico a largo plazo de un bankroll dado un margen conocido.',
    termCode: 'Kelly',
    body:
      'El criterio de Kelly es una fórmula de apuesta desarrollada por John Kelly en 1956 que maximiza la tasa de crecimiento geométrico de un bankroll. Para una apuesta a cuotas decimales, la fórmula es f = (p × cuota − 1) / (cuota − 1), donde p es la verdadera probabilidad de ganar y f la fracción del bankroll a apostar. El Kelly completo solo es óptimo cuando las probabilidades se conocen exactamente; en la práctica, la incertidumbre del modelo significa que las apuestas Kelly completas son demasiado volátiles. La mayoría de los apostantes profesionales usan por tanto el Kelly fraccional — típicamente el 25–50% de la apuesta Kelly completa — que preserva la mayor parte del crecimiento a largo plazo reduciendo a la mitad el riesgo de drawdown.',
    related: ['expected-value', 'value-bet', 'bankroll'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'pi-rating',
    term: 'Pi-rating',
    shortDefinition:
      'Un sistema de valoración de fuerza específico para el fútbol, sucesor de Elo con ratings local y visitante separados por equipo.',
    body:
      'Los Pi-ratings son un sistema de valoración de fuerza específico para el fútbol propuesto por Constantinou y Fenton (2013) como sucesor de Elo. Cada equipo tiene dos valoraciones numéricas — local y visitante — actualizadas tras cada partido con una función no lineal de la diferencia de goles, limitada para reducir la influencia de las grandes victorias. Las innovaciones clave respecto a Elo son la división explícita local/visitante, que captura con precisión los efectos del campo sin una constante global de ventaja local, y la actualización no lineal de la diferencia de goles, que converge más rápido tras ascensos y descensos.',
    related: ['elo-rating', 'expected-goals'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'catboost',
    term: 'CatBoost',
    shortDefinition:
      'Una biblioteca de árboles de decisión con gradient boosting optimizada para features categóricas y boosting ordenado.',
    body:
      'CatBoost es una biblioteca de árboles de decisión con gradient boosting lanzada por Yandex en 2017. Se diferencia de XGBoost y LightGBM en dos aspectos prácticamente importantes: manejo nativo de features categóricas sin one-hot encoding, y boosting ordenado, que reduce el target leakage durante el entrenamiento. Ambas ventajas importan para la predicción de fútbol, donde la identidad del equipo, el árbitro, el estadio y el día de la semana son features categóricas de alta cardinalidad. Empíricamente, CatBoost supera a XGBoost en aproximadamente 0,003 puntos de ranked probability score en predicciones 1X2 sin ajuste de hiperparámetros.',
    related: ['expected-value', 'calibration'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'calibration',
    term: 'Calibración probabilística',
    shortDefinition:
      'La propiedad de que las probabilidades declaradas coincidan con las frecuencias de resultado observadas en muchas predicciones.',
    body:
      'Una estimación de probabilidad está bien calibrada cuando la fracción de positivos entre las predicciones con probabilidad declarada p es igual a p, sobre muchas muestras. Un modelo que dice 70% diez mil veces debería acertar aproximadamente 7.000 veces. La calibración es una cualidad separada de la discriminación: un modelo puede ordenar correctamente los ganadores de los perdedores y aún así citar probabilidades absolutas incorrectas — y un modelo así es inútil para las apuestas porque los cálculos de valor esperado requieren probabilidades correctas. El Expected Calibration Error (ECE) es la medida escalar más común; los modelos de apuestas en producción apuntan a un ECE inferior al 1,5%.',
    related: ['catboost', 'expected-value', 'brier-score'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'closing-line-value',
    term: 'Valor de la cuota de cierre (CLV)',
    shortDefinition:
      'La diferencia entre la cuota a la que se realizó una apuesta y la cuota de cierre al inicio del partido.',
    termCode: 'CLV',
    body:
      'El valor de la cuota de cierre (CLV) mide si un apostante obtiene un precio mejor que el que el mercado establece al inicio del partido. Si apuestas a 2,00 y la cuota de cierre es 1,90, tienes CLV positivo; el mercado se ha movido en contra de tu lado, lo que es fuerte evidencia de que identificaste una ventaja antes de que llegaran apostantes más afilados. El CLV es ampliamente considerado el mejor indicador adelantado del beneficio de apuestas a largo plazo porque las cuotas de cierre son el precio más eficiente que produce el mercado. Un CLV medio positivo sobre una muestra grande implica casi siempre un ROI esperado positivo.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'btts',
    term: 'Ambos equipos marcan (BTTS)',
    shortDefinition:
      'Un mercado de fútbol que se liquida como Sí si ambos equipos marcan al menos un gol y No en caso contrario.',
    termCode: 'BTTS',
    body:
      'Ambos equipos marcan (BTTS) es un mercado de fútbol binario que se liquida como Sí cuando ambos equipos marcan al menos un gol durante el tiempo reglamentario y No en caso contrario. Es popular porque un solo gol tardío puede convertir un boleto perdedor. Desde una perspectiva de modelización, el BTTS se deriva de la distribución conjunta de los goles locales y visitantes: bajo un modelo de Poisson bivariado de Dixon-Coles, P(BTTS=Sí) = 1 − P(GL=0) − P(GV=0) + P(GL=0, GV=0). Las tasas base de BTTS a nivel de liga se sitúan típicamente entre el 48 y el 58%.',
    related: ['over-under-2-5', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'over-under-2-5',
    term: 'Más/Menos de 2,5 goles',
    shortDefinition:
      'Un mercado de fútbol que se liquida como Más si se marcan tres o más goles y Menos si se marcan dos o menos.',
    body:
      'Más/Menos de 2,5 goles es el mercado de goles de fútbol más negociado del mundo. Se liquida como Más cuando se marcan tres o más goles en el tiempo reglamentario y Menos cuando se marcan dos o menos; el medio gol evita los resultados de empate. Como el BTTS, se deriva de la distribución conjunta de goles: con un modelo de Poisson Dixon-Coles se calcula P(Más de 2,5) = 1 − P(goles totales ≤ 2). Las tasas base de las ligas varían desde aproximadamente el 47% en las ligas defensivas hasta el 58% en las ligas goleadoras como la Bundesliga.',
    related: ['btts', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
];

export default entries;
