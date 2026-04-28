import type { GlossaryEntry } from './en';

const LAST_UPDATED = '2026-04-28';

const entries: readonly GlossaryEntry[] = [
  {
    slug: 'value-bet',
    term: 'Value bet',
    shortDefinition:
      'Una scommessa la cui vera probabilità di vincita supera la probabilità implicita del bookmaker, dando un valore atteso positivo.',
    body:
      'Una value bet è qualsiasi scommessa in cui la probabilità stimata del risultato, moltiplicata per la quota decimale, è maggiore di 1. Il prodotto è il valore atteso (VA), e una value bet è per definizione qualsiasi scommessa con VA superiore a 1,0. La probabilità implicita del mercato è 1 / quota_decimale, ma le quote 1X2 grezze includono un margine del 4–8% del bookmaker; per confrontare onestamente, le tre probabilità implicite devono essere normalizzate in modo che sommino a 1,0. Il value betting è l\'unica strategia redditizia a lungo termine nelle scommesse sportive perché è indipendente dal fatto che vinca il favorito o l\'outsider. I risultati a breve termine sono rumorosi; le value bet diventano redditizie solo su centinaia di scommesse con puntate disciplinate.',
    related: ['expected-value', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'expected-value',
    term: 'Valore atteso (VA)',
    shortDefinition:
      'Il profitto o la perdita media di una scommessa per unità puntata, calcolato come probabilità × quota meno uno.',
    termCode: 'VA',
    body:
      'Il valore atteso (VA) è il risultato medio a lungo termine di una scommessa ripetuta, espresso per unità puntata. Per una scommessa a quote decimali la formula è VA = p × quota − 1, dove p è la vera probabilità di vincere. Un VA positivo significa che, ripetuto abbastanza volte con una corretta gestione del bankroll, la scommessa sarà mediamente redditizia. Il VA è il singolo concetto più importante nelle scommesse sportive perché separa la competenza dalla fortuna: brevi sequenze di risultati sono dominate dalla varianza, ma il VA determina la direzione del lungo periodo. Una scommessa può perdere nove volte su dieci ed essere comunque stata la decisione corretta se il suo VA era positivo.',
    related: ['value-bet', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'implied-probability',
    term: 'Probabilità implicita',
    shortDefinition:
      'La probabilità incorporata nella quota di un bookmaker, uguale a 1 / quota_decimale prima della rimozione del margine.',
    body:
      'La probabilità implicita è la probabilità che le quote decimali di un bookmaker suggeriscono per un risultato, calcolata come 1 / quota_decimale. Le probabilità implicite 1X2 grezze sommano a più del 100% — tipicamente 104–108% — perché i bookmaker incorporano un margine, detto anche overround o vig. Per confrontare correttamente la probabilità di mercato con un modello, le tre probabilità implicite grezze devono essere normalizzate dividendo ciascuna per la loro somma, in modo che totalizzino esattamente 1,0. Solo le probabilità implicite normalizzate rappresentano la visione onesta del bookmaker. La differenza tra i numeri grezzi e normalizzati del bookmaker è esattamente il vantaggio della casa su quel mercato.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'kelly-criterion',
    term: 'Criterio di Kelly',
    shortDefinition:
      'Una formula per la dimensione della puntata che massimizza la crescita geometrica a lungo termine di un bankroll dato un vantaggio noto.',
    termCode: 'Kelly',
    body:
      'Il criterio di Kelly è una formula di puntata sviluppata da John Kelly nel 1956 che massimizza il tasso di crescita geometrica di un bankroll. Per una scommessa a quote decimali la formula è f = (p × quota − 1) / (quota − 1), dove p è la vera probabilità di vincere e f la frazione di bankroll da puntare. Il Kelly pieno è ottimale solo quando le probabilità sono note esattamente; in pratica, l\'incertezza del modello significa che le puntate Kelly piene sono troppo volatili. La maggior parte dei professionisti usa quindi il Kelly frazionato — tipicamente il 25–50% della puntata Kelly piena — che preserva la maggior parte della crescita a lungo termine dimezzando il rischio di drawdown.',
    related: ['expected-value', 'value-bet', 'bankroll'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'pi-rating',
    term: 'Pi-rating',
    shortDefinition:
      'Un sistema di valutazione della forza specifico per il calcio, successore di Elo con rating casa e trasferta separati per squadra.',
    body:
      'I Pi-rating sono un sistema di valutazione della forza specifico per il calcio proposto da Constantinou e Fenton (2013) come successore di Elo. Ogni squadra ha due valutazioni numeriche — casa e trasferta — aggiornate dopo ogni partita con una funzione non lineare della differenza reti, limitata per ridurre l\'influenza delle vittorie nette. Le innovazioni chiave rispetto a Elo sono la divisione esplicita casa/trasferta, che cattura accuratamente gli effetti del campo senza una costante globale di vantaggio casalingo, e l\'aggiornamento non lineare della differenza reti, che converge più rapidamente dopo promozioni e retrocessioni.',
    related: ['elo-rating', 'expected-goals'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'catboost',
    term: 'CatBoost',
    shortDefinition:
      'Una libreria di alberi decisionali a gradient boosting ottimizzata per feature categoriali e boosting ordinato.',
    body:
      'CatBoost è una libreria di alberi decisionali a gradient boosting rilasciata da Yandex nel 2017. Si differenzia da XGBoost e LightGBM in due modi praticamente importanti: gestione nativa delle feature categoriali senza one-hot encoding, e boosting ordinato, che riduce il target leakage durante il training. Entrambi i vantaggi contano per la previsione calcistica, dove l\'identità della squadra, l\'arbitro, lo stadio e il giorno della settimana sono feature categoriali ad alta cardinalità. Empiricamente, CatBoost supera XGBoost di circa 0,003 punti di ranked probability score sulle previsioni 1X2 senza alcun tuning degli iperparametri.',
    related: ['expected-value', 'calibration'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'calibration',
    term: 'Calibrazione probabilistica',
    shortDefinition:
      'La proprietà per cui le probabilità dichiarate corrispondono alle frequenze di esito osservate su molte previsioni.',
    body:
      'Una stima di probabilità è ben calibrata quando la frazione di positivi tra le previsioni con probabilità dichiarata p è uguale a p, su molti campioni. Un modello che dice 70% diecimila volte dovrebbe avere ragione circa 7.000 volte. La calibrazione è una qualità separata dalla discriminazione: un modello può ordinare correttamente i vincitori dai perdenti eppure citare probabilità assolute errate — e un tale modello è inutile per le scommesse perché i calcoli del valore atteso richiedono probabilità corrette. L\'Expected Calibration Error (ECE) è la misura scalare più comune; i modelli di scommesse in produzione puntano a un ECE inferiore all\'1,5%.',
    related: ['catboost', 'expected-value', 'brier-score'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'closing-line-value',
    term: 'Valore della quota di chiusura (CLV)',
    shortDefinition:
      'La differenza tra la quota a cui è stata piazzata una scommessa e la quota di chiusura al calcio d\'inizio.',
    termCode: 'CLV',
    body:
      'Il valore della quota di chiusura (CLV) misura se un scommettitore ottiene un prezzo migliore di quello che il mercato stabilisce al calcio d\'inizio. Se scommetti a 2,00 e la quota di chiusura è 1,90, hai un CLV positivo; il mercato si è mosso contro il tuo lato, il che è una forte evidenza che hai identificato un vantaggio prima che arrivassero scommettitori più affilati. Il CLV è ampiamente considerato il miglior indicatore anticipatore di profitto scommessa a lungo termine perché le quote di chiusura rappresentano il prezzo più efficiente che il mercato produce. Un CLV medio positivo su un grande campione implica quasi sempre un ROI atteso positivo.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'btts',
    term: 'Entrambe le squadre segnano (BTTS)',
    shortDefinition:
      'Un mercato calcistico che si regola Sì se entrambe le squadre segnano almeno un gol e No altrimenti.',
    termCode: 'BTTS',
    body:
      'Entrambe le squadre segnano (BTTS) è un mercato calcistico binario che si regola Sì quando entrambe le squadre segnano almeno un gol durante il tempo regolamentare e No altrimenti. È popolare perché un singolo gol tardivo può convertire un biglietto perdente. Dal punto di vista della modellizzazione, il BTTS è derivato dalla distribuzione congiunta dei gol casa e trasferta: sotto un modello di Poisson bivariato di Dixon-Coles, P(BTTS=Sì) = 1 − P(GC=0) − P(GT=0) + P(GC=0, GT=0). I tassi base BTTS a livello di lega si collocano tipicamente tra il 48 e il 58%.',
    related: ['over-under-2-5', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'over-under-2-5',
    term: 'Over/Under 2,5 gol',
    shortDefinition:
      'Un mercato calcistico che si regola Over se vengono segnati tre o più gol e Under se due o meno.',
    body:
      'Over/Under 2,5 gol è il mercato gol calcistici più scambiato al mondo. Si regola Over quando tre o più gol vengono segnati nel tempo regolamentare e Under quando ne vengono segnati due o meno; il mezzo gol evita i risultati di pareggio. Come il BTTS, è derivato dalla distribuzione congiunta dei gol: con un modello di Poisson Dixon-Coles si calcola P(Over 2,5) = 1 − P(gol totali ≤ 2). I tassi base delle leghe variano da circa il 47% nelle leghe difensive al 58% nelle leghe prolifiche come la Bundesliga.',
    related: ['btts', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
];

export default entries;
