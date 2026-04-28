import type { LearnArticle } from './types';

const LAST_UPDATED = '2026-04-01';

const articles: Record<string, LearnArticle> = {
  'value-bets': {
    slug: 'value-bets',
    title: 'Value bets en fútbol: definición y cómo encontrarlas',
    description:
      'Una value bet es una apuesta cuya probabilidad real de ganar está por encima de la probabilidad implícita que marca la casa de apuestas. Aquí aprenderás a detectarla — con ejemplos.',
    tldr:
      'Una value bet existe cuando tu probabilidad estimada es mayor que la probabilidad de mercado ajustada por margen de la casa. El valor esperado es positivo, aunque una apuesta concreta se pierda.',
    sections: [
      {
        heading: 'Definición',
        paragraphs: [
          'Una value bet es cualquier apuesta en la que (tu probabilidad estimada) × (cuota decimal) > 1. Ese producto se llama valor esperado (EV). Solo el EV positivo importa a largo plazo — el resultado de un partido aislado es ruido.',
          'La probabilidad implícita de mercado es 1 / cuota, pero las cuotas 1X2 brutas incluyen un margen de la casa de 4–8 %. Primero hay que eliminar ese margen para comparar de forma justa.',
        ],
      },
      {
        heading: 'Cómo encontrar value bets',
        paragraphs: [
          'Usa un modelo con probabilidades calibradas para local, empate y visitante. Convierte las tres cuotas en probabilidades implícitas, normalízalas para que sumen 1 y compáralas con el modelo. Cuando el modelo está al menos 2–3 puntos porcentuales por encima, hay potencial de value.',
          'El tamaño de la apuesta es tan importante como detectar la ventaja. Kelly fraccional (normalmente 25–50 % de Kelly completo) maximiza el crecimiento a largo plazo sin arruinarte en una mala semana.',
        ],
      },
      {
        heading: 'Por qué la mayoría de los "tips" no son value bets',
        paragraphs: [
          'Las webs de pronósticos impulsadas por afiliación eligen el resultado más probable, no el mejor mal valorado. Adivinar favoritos no tiene nada que ver con value — un favorito a cuota 1,20 con 90 % de probabilidad real tiene EV 1,08; un tapado a 4,50 con 25 % de probabilidad real tiene EV 1,125. El tapado es la value bet.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Las value bets garantizan beneficios?',
        answer:
          'No. Las value bets son positivas en valor esperado, no en cada partido. En 100 apuestas la varianza puede ser muy alta; solo se vuelve realmente medible con varios cientos.',
      },
      {
        question: '¿Qué ventaja mínima necesito?',
        answer:
          'La mayoría de los profesionales exige una ventaja de ≥ 3–5 % después de tener en cuenta la incertidumbre del modelo y el margen de la casa, para compensar la varianza y los costes de ejecución.',
      },
      {
        question: '¿Por qué la casa ofrece value bets?',
        answer:
          'Las casas de apuestas fijan precios para el cliente medio. Las casas blandas reaccionan despacio a lesiones, alineaciones y dinero sharp — ese retraso es la fuente del value.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-01',
  },

  'implied-probability': {
    slug: 'implied-probability',
    title: 'Probabilidad implícita a partir de cuotas: fórmula y eliminación del margen',
    description:
      'Convierte cuotas decimales, fraccionarias y americanas en probabilidades implícitas — y aprende a eliminar el margen de la casa para que los tres resultados sumen 100 %.',
    tldr:
      'Probabilidad implícita = 1 / cuota decimal. Como las tres probabilidades 1X2 suman más de 100 % (overround), debes dividir cada una por la suma total para obtener la probabilidad sin margen.',
    sections: [
      {
        heading: 'La fórmula',
        paragraphs: [
          'Para cuotas decimales: implícita = 1 / cuota. Cuota 2,00 equivale a 50 %, cuota 4,00 equivale a 25 %.',
          'Para cuotas fraccionarias (por ejemplo 5/2): implícita = denominador / (numerador + denominador) = 2/7 ≈ 28,6 %.',
          'Para cuotas americanas: positivas (+150) → 100 / (150+100) = 40 %; negativas (-200) → 200 / (200+100) = 66,7 %.',
        ],
      },
      {
        heading: 'Eliminación del margen',
        paragraphs: [
          'Suma las tres probabilidades implícitas 1X2. Si la suma es 1,06, el overround es del 6 %. Divide cada probabilidad implícita por 1,06 — esa es la estimación "real" de la casa, la que comparas con tu modelo.',
          'Para mercados de dos vías como over/under se aplica la misma lógica — divide por la suma de las dos probabilidades implícitas.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿El margen se reparte siempre por igual?',
        answer:
          'No. Las casas cargan más margen sobre favoritos o tapados, según el sesgo del cliente. La eliminación proporcional es una aproximación; métodos mejores son Shin y Power.',
      },
      {
        question: '¿Por qué mi probabilidad sin margen parece demasiado baja?',
        answer:
          'Porque las cuotas brutas siempre exageran la convicción de la casa en la medida del margen. Quitar el margen muestra la verdadera percepción del mercado.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'kelly-criterion': {
    slug: 'kelly-criterion',
    title: 'Criterio de Kelly para apuestas deportivas: fórmula, ejemplos y límites',
    description:
      'El criterio de Kelly dimensiona cada apuesta para maximizar el crecimiento geométrico a largo plazo. Aquí tienes la fórmula, un ejemplo de fútbol y por qué se usa Kelly fraccional.',
    tldr:
      'Apuesta Kelly = (b·p − q) / b, con b = cuota − 1, p tu probabilidad de ganar y q = 1 − p. Los profesionales suelen usar solo una cuarta parte o la mitad para controlar la varianza.',
    sections: [
      {
        heading: 'Fórmula y ejemplo numérico',
        paragraphs: [
          'Estimas que Manchester City vence a Arsenal con probabilidad 0,55. Cuota 2,10 (b = 1,10). Kelly = (1,10 × 0,55 − 0,45) / 1,10 = 0,155 / 1,10 ≈ 14,1 % de la bankrol.',
          'Kelly a la mitad sería 7 %, Kelly a un cuarto 3,5 %. Kelly completo solo es matemáticamente óptimo si tus probabilidades son exactas — y nunca lo son.',
        ],
      },
      {
        heading: 'Por qué Kelly fraccional',
        paragraphs: [
          'Kelly completo es brutalmente volátil: incluso un estimador imparcial con ruido realista genera caídas del 30–50 %. Kelly fraccional sacrifica un poco de rentabilidad a largo plazo a cambio de drawdowns mucho menores — normalmente un buen intercambio.',
          'Limita cada apuesta individual, independientemente de Kelly, al 1–3 % de la bankrol y evita por completo las apuestas con EV negativo.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Qué pasa si Kelly es cero o negativo?',
        answer:
          'No apostar. Un valor Kelly negativo significa que la apuesta, a las cuotas ofrecidas, tiene un valor esperado negativo.',
      },
      {
        question: '¿Funciona Kelly con combinadas?',
        answer:
          'Técnicamente sí, pero la varianza de las combinadas es tan alta que los tamaños Kelly se vuelven minúsculos. La mayoría de los quants evita las combinadas, salvo como cobertura.',
      },
      {
        question: '¿Cómo dimensiono varias apuestas en paralelo?',
        answer:
          'Usa Kelly simultáneo: resuelve una pequeña optimización que dimensiona todas las apuestas juntas bajo un límite total de exposición. O aplica Kelly individual y limita la exposición total al 25–30 % de la bankrol.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'bankroll-management': {
    slug: 'bankroll-management',
    title: 'Gestión de bankrol en apuestas de fútbol: guía práctica',
    description:
      'La gestión de bankrol es la disciplina de elegir tamaños de apuesta para sobrevivir a la varianza el tiempo suficiente como para que tu ventaja se manifieste. Estas son las reglas que de verdad funcionan.',
    tldr:
      'Trata tu bankrol como un fondo separado y fijo. Arriesga 0,5–2 % por apuesta, no persigas pérdidas y revisa los tamaños mensualmente — no después de cada victoria o derrota.',
    sections: [
      {
        heading: 'Las cinco reglas',
        paragraphs: [
          '1. Solo apostar dinero cuya pérdida puedas asumir. Nunca alquiler, ahorros ni dinero prestado.',
          '2. 1 % de la bankrol por apuesta como estándar; Kelly fraccional solo si tus probabilidades están calibradas.',
          '3. Registrar cada apuesta (fecha, mercado, cuota, stake, resultado, probabilidad del modelo). Sin registro no hay ventaja.',
          '4. Redimensionar mensualmente, no a diario. Aumentar la exposición después de una semana buena es la trampa clásica de la varianza.',
          '5. Fijar stop-loss (por ejemplo, −25 % de la bankrol activa una revisión del modelo) y stop-win (al +50 % asegurar la mitad de las ganancias).',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Qué tamaño debe tener una bankrol inicial?',
        answer:
          'Una cantidad cuya pérdida no cambie tu vida. Muchos apostadores serios empiezan con 100 veces su apuesta habitual.',
      },
      {
        question: '¿Debo retirar las ganancias?',
        answer:
          'Sí, regularmente. Las ganancias realizadas nunca regresan. Muchos apostadores retiran automáticamente el 50 % de cada ganancia mensual.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'closing-line-value': {
    slug: 'closing-line-value',
    title: 'Closing Line Value (CLV): el mejor indicador del ROI a largo plazo',
    description:
      'CLV mide cuánto mejores fueron las cuotas que tomaste respecto a las cuotas al inicio del partido. Es el mejor indicador temprano de rentabilidad.',
    tldr:
      'Closing Line Value (CLV) = (tu_cuota / cuota_final) − 1. Un CLV positivo de forma constante es prueba estadística de ventaja — incluso antes de que lleguen los resultados.',
    sections: [
      {
        heading: 'Por qué CLV importa más que el ROI a corto plazo',
        paragraphs: [
          'El ROI en 50 apuestas es sobre todo ruido. El CLV converge mucho más rápido: 200 apuestas suelen bastar para confirmar un CLV medio de +2 % como algo real, mientras que 200 apuestas dicen casi nada sobre el ROI.',
          'Los sharps y modeladores se evalúan por CLV en los primeros 6–12 meses. Si el CLV es positivo, acabará llegando la bankrol.',
        ],
      },
      {
        heading: 'Cómo medirlo',
        paragraphs: [
          'Registra las cuotas finales 1X2 (Pinnacle es el estándar de oro) y compáralas con las cuotas que tomaste. Tu CLV es positivo si tus cuotas fueron más altas.',
          'Saca la media del CLV por apuesta. Incluso un +1,5 % de CLV medio después del margen de la casa señala una estrategia rentable en casas sharp.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Dónde consigo cuotas finales fiables?',
        answer:
          'Pinnacle es el mercado de referencia de facto. Archivos públicos como oddsportal.com y los CSV de football-data.co.uk contienen cuotas finales de miles de partidos históricos.',
      },
      {
        question: '¿Puede una apuesta tener CLV positivo y aun así perder?',
        answer:
          'Claro — CLV mide habilidad de pricing, no suerte. A lo largo de cientos de apuestas, un CLV positivo se traduce en ROI positivo; en un solo partido, el resultado es ruido.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'expected-goals-xg': {
    slug: 'expected-goals-xg',
    title: 'Expected Goals (xG) explicado: cómo funciona y qué revela',
    description:
      'Expected Goals (xG) asigna a cada disparo una probabilidad de gol — basada en la posición, el tipo y el contexto. Qué mide xG, qué no, y cómo usarlo para apostar.',
    tldr:
      'xG es la suma de las probabilidades de gol por disparo. A lo largo de una temporada, el xG de equipo es mucho más útil para predecir resultados futuros que los goles marcados — la varianza domina las muestras cortas.',
    sections: [
      {
        heading: 'Qué características usa un modelo xG',
        paragraphs: [
          'Cada disparo se evalúa con variables como distancia a portería, ángulo, parte del cuerpo, tipo de pase (pase al hueco vs centro), presión defensiva y estado del partido. El modelo devuelve una probabilidad de 0–1 por tiro.',
          'El xG de un equipo por partido es la suma de esas probabilidades. A lo largo de 38 partidos, un equipo de Premier League con +0,5 xG/partido por encima de la media de la liga casi seguro termina entre los seis primeros.',
        ],
      },
      {
        heading: 'Cómo usar xG para pronosticar partidos',
        paragraphs: [
          'Los xG-for y xG-against móviles de 5–10 partidos son mejores variables que la diferencia de goles pura, porque eliminan la varianza del remate y las rachas calientes de los porteros.',
          'Combina xG con la calidad del disparo (xG por tiro) para identificar equipos que generan ocasiones de forma distinta — los equipos de calidad de ocasión son más sostenibles que los de cantidad de ocasión.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Es xG mejor que los goles?',
        answer:
          'Para pronosticar partidos futuros, casi siempre sí. Para describir lo ocurrido, ganan los goles — solo ellos cuentan en la tabla.',
      },
      {
        question: '¿Por qué se contradicen los modelos xG?',
        answer:
          'Distintos proveedores usan diferentes variables y datos de entrenamiento. Usa un modelo de forma consistente; las comparaciones relativas importan más que los valores absolutos.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'btts-explained': {
    slug: 'btts-explained',
    title: 'Ambos equipos marcan (BTTS): estrategia, cuotas y errores típicos',
    description:
      'BTTS paga cuando ambos equipos anotan al menos un gol. Cómo lo valora el mercado, cuándo está mal fijado y qué mirar en los perfiles de los equipos.',
    tldr:
      'BTTS Sí es rentable cuando se enfrentan dos equipos ofensivos con defensas vulnerables — cuotas típicas 1,65–1,90. El xG puro es un fuerte predictor; la mera varianza en la finalización no lo es.',
    sections: [
      {
        heading: 'Cuándo BTTS Sí tiene value',
        paragraphs: [
          'Busca equipos que generen cada uno ≥ 1,3 xG-for y ≥ 1,0 xG-against por partido en los últimos 10 encuentros. Los equipos de ataque de mitad de tabla históricamente rinden bien en BTTS.',
          'Evita BTTS Sí en partidos con defensas élite y porteros fuertes — producen demasiados resultados de "portería a cero".',
        ],
      },
      {
        heading: 'BTTS No: la jugada contraria',
        paragraphs: [
          'BTTS No está infravalorado cuando hay favorito claro + rival débil en defensa: el favorito suele ganar sin encajar. Las medias de liga ayudan: históricamente la Serie A tiene tasas más altas de BTTS No que la Bundesliga.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Qué significa "BTTS Sí y Más de 2,5"?',
        answer:
          'Un mercado combinado: ambos equipos deben marcar Y el total de goles debe ser ≥ 3. Más exigente, con cuotas más largas.',
      },
      {
        question: '¿BTTS es más fácil de predecir que 1X2?',
        answer:
          'Es un resultado binario, así que es más fácil de calibrar. Pero el margen en BTTS suele ser mayor que en 1X2 — la ventaja por apuesta normalmente es menor.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'over-under-2-5': {
    slug: 'over-under-2-5',
    title: 'Más/Menos 2,5 goles: cómo funciona el mercado y cómo superarlo',
    description:
      'Más de 2,5 paga con 3+ goles. Así puedes pronosticar totales de goles usando xG, contexto de liga y señales de ritmo.',
    tldr:
      'Más/Menos 2,5 se liquida en el umbral de 3 goles. Pronostícalo a partir de xG-for combinado + xG-against del rival, media de liga y efectos local/visitante.',
    sections: [
      {
        heading: 'Modelización del total de goles',
        paragraphs: [
          'Un modelo Poisson sencillo usa los goles esperados de ambos equipos + goles encajados del rival, ajustados por la media de la liga. Un total esperado combinado de ≥ 2,7 respalda una inclinación al Más de 2,5 con cuotas justas.',
        ],
      },
      {
        heading: 'Errores comunes',
        paragraphs: [
          'El sesgo de recencia es el asesino. Un 4:0 en el último partido empuja a los apostadores casuales hacia el Over; el modelo apenas debería moverse porque los goles esperados cambian poco.',
          'Ignorar el clima y las condiciones del césped en invierno — un campo pesado o viento fuerte reducen la línea de goles de forma fiable.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Cuál es la tasa histórica del Más de 2,5 a largo plazo?',
        answer:
          'En las cinco grandes ligas ronda el 53–55 %. Con una cuota típica de 1,85, el punto de equilibrio requiere un 54,1 % — un mercado muy ajustado.',
      },
      {
        question: '¿Qué es el Asian Handicap en Más de 2,5?',
        answer:
          'Los mercados Asian Total desplazan la línea en 0,25 o 0,5 para evitar resultados push. Más de 2,75 divide la apuesta entre Más de 2,5 y Más de 3,0.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  '1x2-explained': {
    slug: '1x2-explained',
    title: 'Apuesta 1X2 explicada: el mercado de fútbol más líquido',
    description:
      '1X2 es una apuesta a tres vías sobre victoria local (1), empate (X) o victoria visitante (2). Cómo se valora, por qué varían los márgenes y dónde está el value.',
    tldr:
      '1X2 es el mercado de fútbol más profundo y líquido. Las tres probabilidades implícitas suman 104–108 % — el overround. Tras quitar el margen, obtienes la verdadera percepción del mercado.',
    sections: [
      {
        heading: 'Cómo se fija el precio del mercado',
        paragraphs: [
          'Las casas sharp como Pinnacle valoran 1X2 con 100,5–101 % (margen inferior al 2 %). Las casas recreativas cargan 5–8 % de margen. Compara siempre varias casas antes de apostar.',
          'Los empates son sistemáticamente más difíciles de pronosticar que las victorias — la probabilidad implícita del empate suele moverse en el rango estrecho del 22–28 %, así que la mayoría de las ventajas están en el lado H o A.',
        ],
      },
      {
        heading: 'Dónde vive el value en 1X2',
        paragraphs: [
          'Las sobre-reacciones del mercado a resultados recientes (victorias 4:0, derrotas en derbi) con muestras pequeñas. Los modelos que ignoran el ruido de corto plazo superan de forma constante a las líneas puestas por humanos en este punto.',
          'Partidos al final de la temporada sin importancia deportiva — el dinero público sobrepremia al equipo aún motivado.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Qué es "1N2" en sitios de apuestas franceses?',
        answer:
          'Es idéntico a 1X2: 1 = victoria local, N = Nul (empate), 2 = victoria visitante. Solo cambia la notación, no el mercado.',
      },
      {
        question: '¿Debería apostar al empate?',
        answer:
          'Solo si tu probabilidad calibrada supera la implícita. En partidos igualados, el empate se comporta casi como un cara o cruz; muchos modelos simplemente se ajustan mal.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'model-accuracy-brier-calibration': {
    slug: 'model-accuracy-brier-calibration',
    title: 'Cómo evaluar modelos de pronóstico de fútbol: Brier, RPS y calibración',
    description:
      'La tasa de acierto es una mala métrica para modelos probabilísticos. Brier Score, RPS y diagramas de fiabilidad muestran si un modelo está realmente calibrado.',
    tldr:
      'Usa Brier Score y Ranked Probability Score (RPS) para comparar modelos, y un diagrama de fiabilidad para comprobar si los "70 %" realmente ganan el 70 % de las veces.',
    sections: [
      {
        heading: 'Por qué la tasa de acierto engaña',
        paragraphs: [
          'Un modelo que siempre elige al favorito alcanza ~52 % de acierto en la Premier League — pero no aporta ninguna ventaja sobre la casa. La tasa de acierto solo evalúa el argmax, no las probabilidades.',
        ],
      },
      {
        heading: 'Brier Score y RPS',
        paragraphs: [
          'Brier = error cuadrático medio entre el vector de probabilidades y el resultado one-hot. Menor es mejor.',
          'RPS (Ranked Probability Score) es el primo ordinal de Brier: penaliza más las predicciones confiadas y erróneas en resultados vecinos — el estándar de facto para 1X2.',
        ],
      },
      {
        heading: 'Diagramas de fiabilidad',
        paragraphs: [
          'Agrupa todas las probabilidades predichas en, por ejemplo, 10 bins. Representa la probabilidad predicha por bin frente a la tasa real de acierto. Un modelo perfectamente calibrado cae sobre la diagonal.',
          'Publicamos el diagrama de fiabilidad de las predicciones en vivo en /performance.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Qué rango de RPS es bueno para 1X2 en fútbol?',
        answer:
          'Las cinco grandes ligas están en 0,19–0,21 para modelos bien calibrados. Por debajo de 0,20 es muy fuerte; por encima de 0,22 sugiere problemas de calibración.',
      },
      {
        question: '¿Por qué no usar simplemente Log-Loss?',
        answer:
          'Log-Loss penaliza infinitamente las predicciones confiadas y erróneas. Brier es más robusto frente a aciertos raros; RPS respeta la estructura ordinal de H/D/A.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'catboost-vs-xgboost': {
    slug: 'catboost-vs-xgboost',
    title: 'CatBoost vs XGBoost para predicción de fútbol: comparación práctica',
    description:
      'Una comparación directa de CatBoost y XGBoost para la predicción 1X2 en fútbol — manejo de categóricas, velocidad de entrenamiento, calibración, RPS y cuándo elegir cada uno.',
    tldr:
      'Ambas bibliotecas alcanzan una precisión predictiva casi idéntica en datos tabulares de fútbol. CatBoost gana en manejo nativo de categóricas y calibración; XGBoost en velocidad de entrenamiento bruta. Para 1X2 con 70+ features mixtas, CatBoost es la opción predeterminada más segura.',
    sections: [
      {
        heading: 'Diferencias bajo el capó',
        paragraphs: [
          'XGBoost usa crecimiento de árbol por niveles con gradient boosting de segundo orden. Las features categóricas deben codificarse manualmente (one-hot, label-encoding o target-encoding).',
          'CatBoost usa árboles simétricos (oblivious trees) y un esquema de boosting ordenado que previene el target leakage durante la codificación automática de categóricas. Esto lo hace más robusto con los hiperparámetros predeterminados.',
        ],
      },
      {
        heading: 'Comparación empírica en datos de fútbol 1X2',
        paragraphs: [
          'En nuestro conjunto de features Top 5 ligas (70+ features, 5 temporadas de entrenamiento, backtest walk-forward), CatBoost y XGBoost terminan a menos de 0,005 RPS el uno del otro cuando ambos están correctamente ajustados. Los hiperparámetros predeterminados favorecen a CatBoost en ~0,01 RPS.',
          'La calibración es donde CatBoost tiene una ventaja significativa: ECE antes de la post-calibración isotónica es de aproximadamente 2,4% (CatBoost) vs 3,1% (XGBoost). Después de isotónica, ambos caen por debajo del 1,5%.',
        ],
      },
      {
        heading: 'Cuándo elegir CatBoost',
        paragraphs: [
          'Muchas features categóricas de alta cardinalidad (IDs de equipo, árbitro, estadio). CatBoost las codifica de forma segura sin leakage.',
          'Quieres una calibración sólida desde el primer momento y poco tiempo para el ajuste. Los valores predeterminados son indulgentes.',
        ],
      },
      {
        heading: 'Cuándo elegir XGBoost',
        paragraphs: [
          'Tus features son principalmente números densos y ya has codificado las categóricas cuidadosamente.',
          'Necesitas la velocidad de entrenamiento absolutamente más rápida en CPU.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Debería usar LightGBM en su lugar?',
        answer:
          'LightGBM es competitivo y más rápido que XGBoost en datasets grandes. Para < 1M filas de datos de fútbol, la diferencia de velocidad rara vez es significativa; la calibración es el diferenciador clave y CatBoost sigue ganando ahí.',
      },
      {
        question: '¿Un ensemble de ambos supera al mejor modelo individual?',
        answer:
          'Sí, marginalmente. Un promedio 50/50 de probabilidades CatBoost y XGBoost calibradas reduce típicamente el RPS en otros 0,001–0,003 respecto al mejor modelo individual.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

  'pi-ratings-explained': {
    slug: 'pi-ratings-explained',
    title: 'Pi-Ratings explicados: el sistema de clasificación futbolístico de los modelos modernos',
    description:
      'Los Pi-Ratings (Constantinou & Fenton, 2013) son el sistema de clasificación futbolística consciente del campo utilizado en muchos modelos de predicción modernos. Esta guía deriva la regla de actualización, muestra un ejemplo práctico y explica cómo usar los Pi-Ratings como features del modelo.',
    tldr:
      'Los Pi-Ratings asignan a cada equipo una fuerza local y visitante distinta, actualizadas después de cada partido por un término de error ponderado. Superan la posición en la clasificación bruta y Elo en la predicción 1X2 fuera de muestra en 1–2% de precisión, a coste de implementación cero.',
    sections: [
      {
        heading: 'Qué son los Pi-Ratings',
        paragraphs: [
          'Los Pi-Ratings, introducidos por Anthony Costa Constantinou y Norman E. Fenton en 2013, asignan a cada equipo dos ratings: una fuerza local R_H y una fuerza visitante R_A.',
          'La división en dos ratings es lo que hace que los Pi-Ratings sean especialmente adecuados para el fútbol. La ventaja del campo es grande (≈ 0,3 goles en el Top 5) y específica de cada equipo — el Atalanta ha sido históricamente notablemente más fuerte en casa que fuera; el Brighton al revés.',
        ],
      },
      {
        heading: 'La regla de actualización',
        paragraphs: [
          'Antes del partido, la diferencia de goles predicha es: gd_pred = R_H(local) − R_A(visitante).',
          'Después del partido con la diferencia de goles real gd_actual, el error es e = gd_actual − gd_pred. La función de amortiguamiento ψ(e) = sign(e) · 3 · log10(1 + |e|) evita que las grandes derrotas dominen.',
          'Ambos equipos actualizan ambos ratings, con tasas de aprendizaje separadas λ para el lado que acaba de jugar y γ para el lado opuesto (típicamente: λ ≈ 0,06, γ ≈ 0,5·λ).',
        ],
      },
      {
        heading: 'Usar los Pi-Ratings como features del modelo',
        paragraphs: [
          'Features directas: R_H_home, R_H_away, R_A_home, R_A_away, más sus deltas y la diferencia de goles predicha. Estas cinco features derivadas por sí solas alcanzan ~52–54% de precisión en 1X2.',
          'Mejor: introducirlos en un modelo de Poisson. Traducir R_diff en goles esperados local y visitante mediante un mapa lineal aprendido, luego convertir en 1X2 con la distribución de Skellam.',
          'Aún mejor: incluirlos como features en un ensemble CatBoost/XGBoost/MLP junto con xG, días de descanso y forma.',
        ],
      },
    ],
    faqs: [
      {
        question: '¿Son los Pi-Ratings mejores que Elo para el fútbol?',
        answer:
          'Sí, ligeramente. La división local/visitante captura la fuerza específica del campo que un Elo puro no puede. Ambos son dominados por modelos ML basados en features completas, pero los Pi-Ratings siguen siendo un top-3 de features individuales en cualquier modelo 1X2.',
      },
      {
        question: '¿Qué tasa de aprendizaje usar?',
        answer:
          'El paper original usaba λ ≈ 0,06 y γ = 0,5·λ. Recomendamos un grid-search λ ∈ {0,04; 0,05; 0,06; 0,07; 0,08} en una temporada hold-out, optimizando RPS o log-loss.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },
};

export default articles;
