import type { LearnArticle } from './types';

const LAST_UPDATED = '2026-04-01';

const articles: Record<string, LearnArticle> = {
  'value-bets': {
    slug: 'value-bets',
    title: "Value bet nel calcio: definizione e come trovarle",
    description:
      "Una value bet è una scommessa la cui probabilità reale di vincita è superiore alla probabilità implicita dal bookmaker. Qui impari a riconoscerla — con esempi.",
    tldr:
      "Una value bet esiste quando la tua probabilità stimata è più alta della probabilità di mercato corretta per il margine del bookmaker. Il valore atteso è positivo, anche se una singola scommessa può perdere.",
    sections: [
      {
        heading: "Definizione",
        paragraphs: [
          "Una value bet è qualsiasi scommessa in cui (la tua probabilità stimata) × (quota decimale) > 1. Il prodotto si chiama valore atteso (EV). Conta solo l'EV positivo nel lungo periodo — l'esito di una singola partita è rumore.",
          "La probabilità implicita di mercato è 1 / quota, ma le quote 1X2 grezze includono un margine del bookmaker del 4–8 %. Devi prima rimuovere quel margine per confrontare in modo corretto.",
        ],
      },
      {
        heading: "Come trovare value bet",
        paragraphs: [
          "Usa un modello con probabilità calibrate per casa, pareggio e trasferta. Trasforma tutte e tre le quote in probabilità implicite, normalizzale in modo che la somma sia 1 e confrontale con il modello. Dove il modello è più alto di almeno 2–3 punti percentuali, c'è potenziale value.",
          "La dimensione della puntata è importante quanto individuare un edge. Il Kelly frazionario (tipicamente 25–50 % del Kelly pieno) massimizza la crescita nel lungo periodo senza rovinarti in una settimana negativa.",
        ],
      },
      {
        heading: "Perché la maggior parte dei tip non è una value bet",
        paragraphs: [
          "I siti di tipster guidati da affiliazioni scelgono l'esito più probabile, non quello più sottoprezzato. Puntare sui favoriti non ha nulla a che fare con il value — un favorito a quota 1,20 con probabilità reale del 90 % ha EV 1,08; un outsider a quota 4,50 con probabilità reale del 25 % ha EV 1,125. L'outsider è la value bet.",
        ],
      },
    ],
    faqs: [
      {
        question: "Le value bet sono una garanzia di vincita?",
        answer:
          "No. Le value bet sono positive in valore atteso, non in ogni singola partita. Su 100 scommesse la varianza può essere forte; diventa misurabile in modo affidabile solo su diverse centinaia.",
      },
      {
        question: "Quanto deve essere grande almeno l'edge?",
        answer:
          "La maggior parte dei professionisti richiede un edge ≥ 3–5 % dopo aver considerato l'incertezza del modello e il margine del bookmaker, per battere varianza e costi di esecuzione.",
      },
      {
        question: "Perché il bookmaker offre comunque value bet?",
        answer:
          "I bookmaker prezzano per il cliente medio. I soft book reagiscono lentamente a infortuni, formazioni e denaro sharp — questo ritardo è la fonte del value.",
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-01',
  },

  'implied-probability': {
    slug: 'implied-probability',
    title: "Probabilità implicita dalle quote: formula e rimozione del margine",
    description:
      "Converti quote decimali, frazionarie e americane in probabilità implicite — e impara come rimuovere il margine del bookmaker, così che i tre esiti sommino al 100 %.",
    tldr:
      "Probabilità implicita = 1 / quota decimale. Poiché le tre probabilità 1X2 sommano oltre il 100 % (overround), devi dividere ciascuna per la somma totale per ottenere la probabilità senza margine.",
    sections: [
      {
        heading: "La formula",
        paragraphs: [
          "Per le quote decimali: implicita = 1 / quota. Quota 2,00 corrisponde al 50 %, quota 4,00 al 25 %.",
          "Per le quote frazionarie (ad esempio 5/2): implicita = denominatore / (numeratore + denominatore) = 2/7 ≈ 28,6 %.",
          "Per le quote americane: positive (+150) → 100 / (150+100) = 40 %; negative (-200) → 200 / (200+100) = 66,7 %.",
        ],
      },
      {
        heading: "Rimozione del margine",
        paragraphs: [
          "Somma le tre probabilità implicite 1X2. Se la somma è 1,06, l'overround è 6 %. Dividi ogni probabilità implicita per 1,06 — questa è la stima reale del bookmaker da confrontare con il tuo modello.",
          "Per i mercati a due esiti come over/under vale la stessa logica — dividi per la somma delle due probabilità implicite.",
        ],
      },
    ],
    faqs: [
      {
        question: "Il margine è sempre distribuito in modo uniforme?",
        answer:
          "No. I bookmaker applicano più margine su favoriti o outsider, a seconda dei bias dei clienti. La sottrazione proporzionale è un'approssimazione; metodi migliori sono Shin e Power.",
      },
      {
        question: "Perché la mia probabilità senza margine sembra troppo bassa?",
        answer:
          "Perché le quote grezze gonfiano sempre la convinzione del bookmaker di un valore pari al margine. La rimozione del margine mostra la vera valutazione del mercato.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'kelly-criterion': {
    slug: 'kelly-criterion',
    title: "Criterio di Kelly per le scommesse sportive: formula, esempi, limiti",
    description:
      "Il criterio di Kelly dimensiona ogni scommessa in modo da massimizzare la crescita geometrica nel lungo periodo. Ecco formula, esempio sul calcio e motivi per usare il Kelly frazionario.",
    tldr:
      "Puntata Kelly = (b·p − q) / b, con b = quota − 1, p la tua probabilità di vincita e q = 1 − p. I professionisti usano di solito solo un quarto o la metà per controllare la varianza.",
    sections: [
      {
        heading: "Formula ed esempio numerico",
        paragraphs: [
          "Stimi che il Manchester City batta l'Arsenal con probabilità 0,55. Quota 2,10 (b = 1,10). Kelly = (1,10 × 0,55 − 0,45) / 1,10 = 0,155 / 1,10 ≈ 14,1 % della bankroll.",
          "Il mezzo Kelly punterebbe il 7 %, il quarto Kelly il 3,5 %. Il Kelly pieno è matematicamente ottimale solo se le tue probabilità sono esatte — cosa che non accade mai.",
        ],
      },
      {
        heading: "Perché il Kelly frazionario",
        paragraphs: [
          "Il Kelly pieno è brutalmente volatile: persino uno stimatore non distorto con rumore realistico produce drawdown del 30–50 %. Il Kelly frazionario sacrifica un po' di rendimento atteso per drawdown molto più piccoli — di solito è un buon compromesso.",
          "Limita ogni singola scommessa, indipendentemente dal Kelly, all'1–3 % della bankroll ed evita del tutto le scommesse con EV negativo.",
        ],
      },
    ],
    faqs: [
      {
        question: "Cosa succede se Kelly è zero o negativo?",
        answer:
          "Non scommettere. Un valore Kelly negativo significa che, alle quote offerte, la scommessa ha un valore atteso negativo.",
      },
      {
        question: "Kelly funziona con le multiple?",
        answer:
          "Tecnicamente sì, ma la varianza delle multiple è così alta che le puntate Kelly diventano minuscole. La maggior parte dei quant evita le multiple, salvo casi di copertura.",
      },
      {
        question: "Come dimensiono più scommesse contemporanee?",
        answer:
          "Usa il Kelly simultaneo: risolvi una piccola ottimizzazione che dimensiona tutte le scommesse insieme sotto un limite complessivo di puntata. Oppure applica il Kelly singolo e limita l'esposizione totale al 25–30 % della bankroll.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'bankroll-management': {
    slug: 'bankroll-management',
    title: "Gestione della bankroll nel betting sul calcio: guida pratica",
    description:
      "La gestione della bankroll è la disciplina di scegliere le puntate in modo da sopravvivere abbastanza a lungo alla varianza perché il tuo edge possa emergere. Ecco le regole che funzionano davvero.",
    tldr:
      "Tratta la tua bankroll come un pool separato e fisso. Rischia lo 0,5–2 % per scommessa, non inseguire le perdite e rivedi le puntate ogni mese — non dopo ogni vincita o sconfitta.",
    sections: [
      {
        heading: "Le cinque regole",
        paragraphs: [
          "1. Usa solo denaro che puoi permetterti di perdere. Mai affitto, risparmi o soldi presi in prestito.",
          "2. Standard 1 % della bankroll per scommessa; Kelly frazionario solo se le tue probabilità sono calibrate.",
          "3. Registra ogni scommessa (data, mercato, quota, puntata, risultato, probabilità del modello). Senza log non c'è edge.",
          "4. Ridimensiona ogni mese, non ogni giorno. Aumentare dopo una settimana positiva è la classica trappola della varianza.",
          "5. Imposta uno stop-loss (ad esempio −25 % della bankroll attiva un review del modello) e uno stop-win (al +50 % proteggi metà dei guadagni).",
        ],
      },
    ],
    faqs: [
      {
        question: "Quanto grande dovrebbe essere una bankroll iniziale?",
        answer:
          "Un importo la cui perdita non influisca sulla tua vita. Molti scommettitori seri partono con 100 volte la loro puntata abituale.",
      },
      {
        question: "Devo prelevare le vincite?",
        answer:
          "Sì, regolarmente. I profitti realizzati non rientrano mai in gioco. Molti scommettitori prelevano automaticamente il 50 % di ogni utile mensile.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'closing-line-value': {
    slug: 'closing-line-value',
    title: "Closing Line Value (CLV): il miglior indicatore del ROI a lungo termine",
    description:
      "Il CLV misura quanto le quote prese erano migliori rispetto alle quote al calcio d'inizio. È il singolo miglior indicatore anticipato della redditività.",
    tldr:
      "Closing Line Value (CLV) = (tua_quota / quota finale) − 1. Un CLV costantemente positivo è una prova statistica di edge — ancora prima di vedere i risultati.",
    sections: [
      {
        heading: "Perché il CLV conta più del ROI nel breve periodo",
        paragraphs: [
          "Il ROI su 50 scommesse è soprattutto rumore. Il CLV converge molto più in fretta: spesso 200 scommesse bastano per confermare un CLV medio di +2 % come reale, mentre 200 scommesse dicono quasi nulla sul ROI.",
          "Gli sharp e i modellisti vengono giudicati nei primi 6–12 mesi in base al CLV. Se il CLV è positivo, la bankroll segue.",
        ],
      },
      {
        heading: "Come misurarlo",
        paragraphs: [
          "Raccogli le quote finali 1X2 (Pinnacle è il gold standard) e confrontale con le quote prese. Il tuo CLV è positivo se le tue quote erano più alte.",
          "Calcola la media del CLV per scommessa. Già un CLV medio di +1,5 % dopo il margine del bookmaker segnala una strategia redditizia sui book sharp.",
        ],
      },
    ],
    faqs: [
      {
        question: "Dove trovo quote finali affidabili?",
        answer:
          "Pinnacle è il mercato di riferimento de facto. Archivi pubblici come oddsportal.com e i CSV di football-data.co.uk contengono quote finali di migliaia di partite passate.",
      },
      {
        question: "Una scommessa può avere CLV positivo e perdere comunque?",
        answer:
          "Certo — il CLV misura l'abilità di pricing, non la fortuna. Su centinaia di scommesse, un CLV positivo si traduce in ROI positivo; in una singola partita il risultato è rumore.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'expected-goals-xg': {
    slug: 'expected-goals-xg',
    title: "Expected Goals (xG) spiegati: funzionamento e valore predittivo",
    description:
      "Expected Goals (xG) assegna a ogni tiro una probabilità di gol — basata su posizione, tipo e contesto. Cosa misura xG, cosa non misura e come usarlo per scommettere.",
    tldr:
      "xG è la somma delle probabilità di gol per tiro. Su una stagione, l'xG di squadra è molto più utile per prevedere i risultati futuri rispetto ai gol segnati — la varianza domina i campioni brevi.",
    sections: [
      {
        heading: "Quali feature usa un modello xG",
        paragraphs: [
          "Ogni tiro viene valutato con attributi come distanza dalla porta, angolo, parte del corpo, tipo di assist (passaggio filtrante vs cross), pressione difensiva e punteggio. Il modello restituisce una probabilità 0–1 per tiro.",
          "L'xG di una squadra per partita è la somma di queste probabilità. Su 38 partite, una squadra di Premier League con +0,5 xG/partita sopra la media del campionato è quasi certamente tra le prime sei.",
        ],
      },
      {
        heading: "Come usare l'xG nella previsione delle partite",
        paragraphs: [
          "Le metriche rolling di 5–10 partite xG for e xG against sono feature più forti della semplice differenza reti, perché rimuovono la varianza della finalizzazione e le strisce positive dei portieri.",
          "Combina l'xG con la qualità dei tiri (xG per tiro) per identificare le squadre che generano occasioni in modo diverso — le squadre basate sulla qualità delle occasioni sono più sostenibili di quelle basate solo sulla quantità.",
        ],
      },
    ],
    faqs: [
      {
        question: "xG è migliore dei gol?",
        answer:
          "Per prevedere le partite future, quasi sempre sì. Per descrivere ciò che è successo, vincono i gol — contano solo quelli in classifica.",
      },
      {
        question: "Perché i modelli xG non coincidono?",
        answer:
          "Diversi provider usano feature e dati di training differenti. Usa un solo modello in modo coerente; i confronti relativi contano più dei valori assoluti.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'btts-explained': {
    slug: 'btts-explained',
    title: "Entrambe le squadre segnano (BTTS): strategia, quote ed errori tipici",
    description:
      "BTTS paga se entrambe le squadre segnano almeno un gol. Come il mercato prezza, quando sbaglia e a cosa guardare nei profili delle squadre.",
    tldr:
      "BTTS Sì è profittevole quando due squadre offensive con difese fragili si affrontano — quote tipiche 1,65–1,90. Il puro xG è un forte predittore; la sola varianza al tiro no.",
    sections: [
      {
        heading: "Quando BTTS Sì ha value",
        paragraphs: [
          "Cerca squadre che generano ciascuna almeno ≥ 1,3 xG for e ≥ 1,0 xG against per partita nelle ultime 10 gare. Le squadre di fascia media in attacco si comportano storicamente bene sul BTTS.",
          "Evita BTTS Sì nelle partite con difese d'élite e portieri forti — producono troppi risultati a porta inviolata.",
        ],
      },
      {
        heading: "BTTS No: la giocata contrarian",
        paragraphs: [
          "BTTS No è sottovalutato quando c'è un favorito chiaro contro un outsider difensivamente debole: spesso il favorito vince a porta inviolata. I valori medi di lega aiutano: la Serie A ha storicamente tassi di BTTS No più alti della Bundesliga.",
        ],
      },
    ],
    faqs: [
      {
        question: "Cosa significa BTTS Sì e Over 2,5?",
        answer:
          "Un mercato combinato: entrambe le squadre devono segnare E il totale gol deve essere ≥ 3. Più impegnativo, con quote più alte.",
      },
      {
        question: "BTTS è più facile da prevedere dell'1X2?",
        answer:
          "È un esito binario, quindi più semplice da calibrare. Ma il margine sul BTTS è spesso più alto rispetto all'1X2 — il value per scommessa è di solito più piccolo.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'over-under-2-5': {
    slug: 'over-under-2-5',
    title: "Over/Under 2,5 gol: come funziona il mercato e come batterlo",
    description:
      "L'over 2,5 paga con 3+ gol. Ecco come prevedere il totale reti usando xG, contesto di campionato e segnali di ritmo.",
    tldr:
      "Over/Under 2,5 si decide alla soglia dei 3 gol. Prevedilo con xG for combinato + xG against avversario, media del campionato ed effetti casa/trasferta.",
    sections: [
      {
        heading: "Modellare il totale gol",
        paragraphs: [
          "Un semplice modello di Poisson usa i gol attesi di entrambe le squadre + i gol subiti dagli avversari, corretti per la media del campionato. Un totale gol atteso combinato ≥ 2,7 supporta un lean sull'Over 2,5 a quote corrette.",
          "Dixon-Coles affina Poisson correggendo le correlazioni dei risultati bassi (0-0, 1-0, 0-1, 1-1) — uno standard nella modellazione calcistica dal 1997.",
        ],
      },
      {
        heading: "Errori comuni",
        paragraphs: [
          "Il recency bias è il killer. Un 4:0 nell'ultima partita spinge i giocatori occasionali verso l'Over; il modello dovrebbe muoversi poco, perché i gol attesi cambiano appena.",
          "Ignorare meteo e condizioni del campo in inverno — terreno pesante o vento forte abbassano in modo affidabile la soglia gol.",
        ],
      },
    ],
    faqs: [
      {
        question: "Quanto vale l'Over 2,5 nel lungo periodo?",
        answer:
          "Nelle prime 5 leghe europee è intorno al 53–55 %. Con quota tipica 1,85 il break-even richiede il 54,1 % — un mercato stretto.",
      },
      {
        question: "Cosa significa Asian Handicap su Over 2,5?",
        answer:
          "I mercati Asian total spostano la linea di 0,25 o 0,5 per evitare risultati push. Over 2,75 divide la puntata tra Over 2,5 e Over 3,0.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  '1x2-explained': {
    slug: '1x2-explained',
    title: "Scommessa 1X2 spiegata: il mercato calcio più liquido",
    description:
      "1X2 è una scommessa a tre esiti su vittoria casa (1), pareggio (X) o vittoria trasferta (2). Come viene prezzata, perché i margini variano e dove si trova il value.",
    tldr:
      "1X2 è il mercato calcistico più profondo e liquido. Le tre probabilità implicite sommano al 104–108 % — l'overround. Dopo la rimozione del margine emerge la vera stima del mercato.",
    sections: [
      {
        heading: "Come viene prezzato il mercato",
        paragraphs: [
          "I book sharp come Pinnacle prezzano l'1X2 con il 100,5–101 % (margine inferiore al 2 %). I book ricreativi portano il margine al 5–8 %. Confronta sempre più bookmaker prima di scommettere.",
          "I pareggi sono sistematicamente più difficili da prevedere rispetto alle vittorie — la probabilità implicita del pareggio è tipicamente nel range 22–28 %, quindi la maggior parte degli edge è sul lato casa o trasferta.",
        ],
      },
      {
        heading: "Dove vive il value nell'1X2",
        paragraphs: [
          "Sovrarreazioni del mercato a risultati recenti (vittorie 4:0, derby persi) su campioni piccoli. I modelli che ignorano il rumore di breve periodo battono qui con costanza le linee costruite dagli umani.",
          "Partite di fine stagione senza obiettivi sportivi — il denaro del pubblico sovrapprezza la squadra ancora motivata.",
        ],
      },
    ],
    faqs: [
      {
        question: "Cosa significa 1N2 sui siti di scommesse francesi?",
        answer:
          "È identico all'1X2: 1 = vittoria casa, N = Nul (pareggio), 2 = vittoria trasferta. Solo notazione, nessuna differenza.",
      },
      {
        question: "Dovrei puntare sul pareggio?",
        answer:
          "Solo se la tua probabilità calibrata è superiore a quella implicita. Nelle partite equilibrate il pareggio è simile a un coin flip; molti modelli si adattano semplicemente male.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'model-accuracy-brier-calibration': {
    slug: 'model-accuracy-brier-calibration',
    title: "Come valutare i modelli di previsione calcistica: Brier, RPS e calibrazione",
    description:
      "L'accuracy è una metrica scarsa per i modelli probabilistici. Brier Score, RPS e i diagrammi di reliability mostrano se un modello è davvero calibrato.",
    tldr:
      "Usa Brier Score e Ranked Probability Score (RPS) per il confronto, e un diagramma di reliability per verificare se i pronostici '70 %' vincono davvero nel 70 % dei casi.",
    sections: [
      {
        heading: "Perché l'accuracy inganna",
        paragraphs: [
          "Un modello che sceglie sempre il favorito ottiene circa il 52 % di accuracy in Premier League — ma non offre alcun edge sul bookmaker. L'accuracy controlla solo l'argmax, non le probabilità.",
        ],
      },
      {
        heading: "Brier Score e RPS",
        paragraphs: [
          "Brier = errore quadratico medio tra il vettore delle probabilità e l'esito one-hot. Più basso è meglio.",
          "RPS (Ranked Probability Score) è il cugino ordinale del Brier: penalizza più duramente le previsioni errate ma molto confidenti su esiti vicini — lo standard de facto per l'1X2.",
        ],
      },
      {
        heading: "Diagrammi di reliability",
        paragraphs: [
          "Raggruppa tutte le probabilità previste in, ad esempio, 10 bin. Disegna la probabilità prevista per bin contro il tasso reale di successo. Un modello perfettamente calibrato cade sulla diagonale.",
          "Pubbliciamo il diagramma di reliability delle previsioni live su /performance.",
        ],
      },
    ],
    faqs: [
      {
        question: "Qual è un buon intervallo di RPS per l'1X2 nel calcio?",
        answer:
          "Le prime 5 leghe si aggirano tra 0,19–0,21 per modelli ben calibrati. Sotto 0,20 è molto forte; sopra 0,22 indica problemi di calibrazione.",
      },
      {
        question: "Perché non usare semplicemente il log-loss?",
        answer:
          "Il log-loss punisce all'infinito le previsioni errate ma molto confidenti. Brier è più robusto sui colpi isolati rari; RPS rispetta la struttura ordinale di H/D/A.",
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'catboost-vs-xgboost': {
    slug: 'catboost-vs-xgboost',
    title: 'CatBoost vs XGBoost per la previsione calcistica: confronto pratico',
    description:
      'Un confronto diretto tra CatBoost e XGBoost per la previsione 1X2 nel calcio — gestione delle categoriali, velocità di training, calibrazione, RPS e quando scegliere l\'uno o l\'altro.',
    tldr:
      'Entrambe le librerie raggiungono un\'accuratezza predittiva quasi identica su dati tabulari calcistici. CatBoost vince sulla gestione nativa delle categoriali e la calibrazione; XGBoost sulla velocità di training grezza. Per il 1X2 con 70+ feature miste, CatBoost è la scelta predefinita più sicura.',
    sections: [
      {
        heading: 'Differenze sotto il cofano',
        paragraphs: [
          'XGBoost usa la crescita degli alberi per livello con gradient boosting del second\'ordine. Le feature categoriali devono essere codificate manualmente (one-hot, label-encoding o target-encoding).',
          'CatBoost usa alberi simmetrici (oblivious trees) e uno schema di boosting ordinato che previene il target leakage durante la codifica automatica delle categoriali. Questo lo rende più robusto con gli iperparametri predefiniti.',
        ],
      },
      {
        heading: 'Confronto empirico su dati calcio 1X2',
        paragraphs: [
          'Sul nostro set di feature Top 5 leghe (70+ feature, 5 stagioni di training, backtest walk-forward), CatBoost e XGBoost finiscono a meno di 0,005 RPS l\'uno dall\'altro quando entrambi sono correttamente ottimizzati. Gli iperparametri predefiniti favoriscono CatBoost di ~0,01 RPS.',
          'La calibrazione è dove CatBoost ha un vantaggio significativo: ECE prima della post-calibrazione isotonica è circa 2,4% (CatBoost) vs 3,1% (XGBoost). Dopo l\'isotonica, entrambi scendono sotto 1,5%.',
        ],
      },
      {
        heading: 'Quando scegliere CatBoost',
        paragraphs: [
          'Molte feature categoriali ad alta cardinalità (ID squadra, arbitro, stadio). CatBoost le codifica in modo sicuro senza leakage.',
          'Vuoi una calibrazione solida out-of-the-box e poco tempo per il tuning. I default sono permissivi.',
        ],
      },
      {
        heading: 'Quando scegliere XGBoost',
        paragraphs: [
          'Le tue feature sono principalmente numeri densi e hai già codificato attentamente le categoriali.',
          'Hai bisogno della velocità di training più assoluta su CPU.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Dovrei usare LightGBM invece?',
        answer:
          'LightGBM è competitivo e più veloce di XGBoost su dataset grandi. Per < 1M righe di dati calcistici, il gap di velocità è raramente significativo; la calibrazione è il differenziatore chiave e CatBoost vince ancora lì.',
      },
      {
        question: 'Un ensemble di entrambi supera il singolo modello migliore?',
        answer:
          'Sì, marginalmente. Una media 50/50 di probabilità CatBoost e XGBoost calibrate riduce tipicamente il RPS di altri 0,001–0,003 rispetto al miglior modello singolo.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

  'pi-ratings-explained': {
    slug: 'pi-ratings-explained',
    title: 'Pi-Ratings spiegati: il sistema di rating calcistico dei modelli moderni',
    description:
      'I Pi-Ratings (Constantinou & Fenton, 2013) sono il sistema di rating calcistico con consapevolezza del terreno usato in molti modelli di previsione moderni. Questa guida deriva la regola di aggiornamento, mostra un esempio pratico e spiega come usare i Pi-Ratings come feature del modello.',
    tldr:
      'I Pi-Ratings assegnano a ogni squadra una forza casa e trasferta distinte, aggiornate dopo ogni partita da un termine di errore ponderato. Superano la posizione in classifica grezza e Elo nella previsione 1X2 fuori campione di 1–2% di accuratezza, a costo di implementazione zero.',
    sections: [
      {
        heading: 'Cosa sono i Pi-Ratings',
        paragraphs: [
          'I Pi-Ratings, introdotti da Anthony Costa Constantinou e Norman E. Fenton nel 2013, assegnano a ogni squadra due rating: una forza casa R_H e una forza trasferta R_A.',
          'La divisione in due rating è ciò che rende i Pi-Ratings particolarmente adatti al calcio. Il vantaggio del campo è grande (≈ 0,3 gol nei Top 5) e specifico per squadra — l\'Atalanta è storicamente nettamente più forte in casa che in trasferta; il Brighton al contrario.',
        ],
      },
      {
        heading: 'La regola di aggiornamento',
        paragraphs: [
          'Prima del calcio d\'inizio, la differenza gol predetta è: gd_pred = R_H(casa) − R_A(trasferta).',
          'Dopo la partita con differenza gol effettiva gd_actual, l\'errore è e = gd_actual − gd_pred. La funzione di smorzamento ψ(e) = sign(e) · 3 · log10(1 + |e|) impedisce che le grandi sconfitte dominino.',
          'Entrambe le squadre aggiornano entrambi i rating, con tassi di apprendimento separati λ per il lato appena giocato e γ per il lato opposto (tipicamente: λ ≈ 0,06, γ ≈ 0,5·λ).',
        ],
      },
      {
        heading: 'Usare i Pi-Ratings come feature del modello',
        paragraphs: [
          'Feature dirette: R_H_home, R_H_away, R_A_home, R_A_away, più i loro delta e la differenza gol predetta. Queste cinque feature derivate da sole raggiungono ~52–54% di accuratezza sul 1X2.',
          'Meglio: alimentarli in un modello di Poisson. Tradurre R_diff in gol attesi casa e trasferta tramite una mappa lineare appresa, poi convertire in 1X2 con la distribuzione di Skellam.',
          'Ancora meglio: includerli come feature in un ensemble CatBoost/XGBoost/MLP insieme a xG, giorni di riposo e forma.',
        ],
      },
    ],
    faqs: [
      {
        question: 'I Pi-Ratings sono migliori di Elo per il calcio?',
        answer:
          'Sì, leggermente. La divisione casa/trasferta cattura la forza specifica al terreno che un Elo puro non può. Entrambi sono dominati da modelli ML basati su feature complete, ma i Pi-Ratings rimangono una top-3 feature singola in qualsiasi modello 1X2.',
      },
      {
        question: 'Quale tasso di apprendimento usare?',
        answer:
          'Il paper originale usava λ ≈ 0,06 e γ = 0,5·λ. Raccomandiamo un grid-search λ ∈ {0,04; 0,05; 0,06; 0,07; 0,08} su una stagione hold-out, ottimizzando RPS o log-loss.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },
};

export default articles;
