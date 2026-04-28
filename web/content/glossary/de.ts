import type { GlossaryEntry } from './en';

const LAST_UPDATED = '2026-04-28';

const entries: readonly GlossaryEntry[] = [
  {
    slug: 'value-bet',
    term: 'Value Bet',
    shortDefinition:
      'Eine Wette, deren tatsächliche Gewinnwahrscheinlichkeit die implizite Buchmacherwahrscheinlichkeit übersteigt und damit einen positiven Erwartungswert ergibt.',
    body:
      'Eine Value Bet ist jede Wette, bei der die geschätzte Wahrscheinlichkeit des Ergebnisses multipliziert mit der Dezimalquote größer als 1 ist. Das Produkt ist der Erwartungswert (EV), und eine Value Bet ist per Definition jede Wette mit EV über 1,0. Die implizite Marktwahrscheinlichkeit berechnet sich aus 1 / Dezimalquote, doch rohe 1X2-Quoten enthalten eine 4–8-prozentige Buchmachermarge; um fair zu vergleichen, müssen die drei implizierten Wahrscheinlichkeiten normiert werden, sodass sie zusammen 1,0 ergeben. Value Betting ist die einzige langfristig profitable Strategie im Sportwetten, weil sie unabhängig davon ist, ob der Favorit oder der Außenseiter gewinnt — ein 1,20-Favorit mit 90 % wahrer Wahrscheinlichkeit hat EV 1,08, während ein 4,50-Außenseiter mit 25 % wahrer Wahrscheinlichkeit EV 1,125 hat. Der Außenseiter ist die bessere Value Bet, obwohl er viel unwahrscheinlicher ist. Kurzfristige Ergebnisse sind verrauscht; Value Bets werden erst über Hunderte von Wetten mit diszipliniertem Einsatz profitabel.',
    related: ['expected-value', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'expected-value',
    term: 'Erwartungswert (EV)',
    shortDefinition:
      'Der durchschnittliche Gewinn oder Verlust einer Wette pro eingesetzter Einheit, berechnet als Wahrscheinlichkeit × Quote minus eins.',
    termCode: 'EV',
    body:
      'Der Erwartungswert (EV) ist das langfristige Durchschnittsergebnis einer wiederholten Wette, ausgedrückt pro eingesetzter Einheit. Für eine Dezimalquoten-Wette lautet die Formel EV = p × Quote − 1, wobei p die wahre Gewinnwahrscheinlichkeit ist. Ein positiver EV bedeutet, dass die Wette bei ausreichend vielen Wiederholungen mit korrektem Bankroll-Management im Durchschnitt profitabel sein wird. EV ist das einzig wichtige Konzept beim Sportwetten, weil es Können von Glück trennt: Kurze Ergebnisserien werden von Varianz dominiert, aber EV bestimmt die Richtung der langen Frist. Eine Wette kann neun von zehn Mal verlieren und trotzdem die richtige Entscheidung gewesen sein, wenn ihr EV positiv war. Kalibrierte Wahrscheinlichkeitsmodelle sind der einzige praktische Weg, p zuverlässig zu schätzen, und margenbereinigte Buchmacherquoten sind der Maßstab, den es zu schlagen gilt.',
    related: ['value-bet', 'implied-probability', 'kelly-criterion'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'implied-probability',
    term: 'Implizite Wahrscheinlichkeit',
    shortDefinition:
      'Die in einer Buchmacherquote eingebaute Wahrscheinlichkeit, gleich 1 / Dezimalquote vor der Margenbereinigung.',
    body:
      'Die implizite Wahrscheinlichkeit ist die Wahrscheinlichkeit, die die Dezimalquote eines Buchmachers für ein Ergebnis impliziert, berechnet als 1 / Dezimalquote. Rohe 1X2-implizite Wahrscheinlichkeiten summieren sich auf mehr als 100 % — typischerweise 104–108 % — weil Buchmacher eine Marge einbauen, auch Overround oder Vig genannt. Um die Marktwahrscheinlichkeit fair mit einem Modell zu vergleichen, müssen die drei rohen implizierten Wahrscheinlichkeiten normiert werden, indem jede durch ihre Summe geteilt wird, sodass sie genau 1,0 ergeben. Nur normierte implizite Wahrscheinlichkeiten stellen die ehrliche Einschätzung des Buchmachers dar. Die Differenz zwischen rohen und normierten Buchmacherzahlen ist genau der Hausvorteil auf diesem Markt.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'kelly-criterion',
    term: 'Kelly-Kriterium',
    shortDefinition:
      'Eine Formel zur Einsatzgröße, die das langfristige geometrische Wachstum eines Bankrolls bei bekannter Kante maximiert.',
    termCode: 'Kelly',
    body:
      'Das Kelly-Kriterium ist eine von John Kelly 1956 entwickelte Einsatzformel, die die geometrische Wachstumsrate eines Bankrolls maximiert. Für eine Dezimalquoten-Wette lautet die Formel f = (p × Quote − 1) / (Quote − 1), wobei p die wahre Gewinnwahrscheinlichkeit und f der einzusetzende Bankroll-Anteil ist. Full Kelly ist nur optimal, wenn Wahrscheinlichkeiten exakt bekannt sind; in der Praxis bedeutet Modellunsicherheit, dass Full-Kelly-Einsätze zu volatil sind. Die meisten professionellen Wetter verwenden daher fraktionales Kelly — typischerweise 25–50 % des vollen Kelly-Einsatzes — was den größten Teil des langfristigen Wachstums erhält und das Drawdown-Risiko halbiert. Kelly-Sizing gibt null Einsatz für jede Wette mit nicht-positivem EV — das richtige Verhalten: Wetten auf negative-EV-Ergebnisse zerstören einen Bankroll.',
    related: ['expected-value', 'value-bet', 'bankroll'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'pi-rating',
    term: 'Pi-Rating',
    shortDefinition:
      'Ein fußballspezifisches Stärkebewertungssystem, ein Elo-Nachfolger mit separaten Heim- und Auswärtsratings pro Team.',
    body:
      'Pi-Ratings sind ein fußballspezifisches Stärkebewertungssystem, das von Constantinou und Fenton (2013) als Elo-Nachfolger vorgeschlagen wurde. Jedes Team hat zwei numerische Bewertungen — Heim und Auswärts — die nach jedem Spiel mit einer nichtlinearen Funktion des Torverhältnisses aktualisiert werden, wobei hohe Siege gedeckelt werden. Die wichtigsten Innovationen gegenüber Elo sind die explizite Heim-/Auswärts-Aufteilung, die Ortseffekte genau erfasst, und die nichtlineare Torverhältnis-Aktualisierung, die nach Auf- und Abstiegen schneller konvergiert. Empirisch erzielen Pi-Ratings einen niedrigeren Brier-Score als Elo bei Out-of-Sample-Fußballspielen.',
    related: ['elo-rating', 'expected-goals'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'catboost',
    term: 'CatBoost',
    shortDefinition:
      'Eine Gradient-Boosting-Entscheidungsbaum-Bibliothek, optimiert für kategorische Features und geordnetes Boosting.',
    body:
      'CatBoost ist eine Gradient-Boosting-Entscheidungsbaum-Bibliothek, die 2017 von Yandex veröffentlicht wurde. Sie unterscheidet sich von XGBoost und LightGBM in zwei praktisch wichtigen Punkten: native Behandlung kategorischer Features ohne One-Hot-Encoding und geordnetes Boosting, das Target-Leakage während des Trainings reduziert. Beide Vorteile sind bei Fußballvorhersagen wichtig, wo Team-Identität, Schiedsrichter, Stadion und Wochentag hochkardinalitäts-kategorische Features sind. Empirisch übertrifft CatBoost XGBoost um etwa 0,003 Ranked-Probability-Score-Punkte bei 1X2-Fußballvorhersagen ohne Hyperparameter-Tuning.',
    related: ['expected-value', 'calibration'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'calibration',
    term: 'Wahrscheinlichkeitskalibrierung',
    shortDefinition:
      'Die Eigenschaft, dass angegebene Wahrscheinlichkeiten mit den beobachteten Ergebnishäufigkeiten über viele Vorhersagen übereinstimmen.',
    body:
      'Eine Wahrscheinlichkeitsschätzung ist gut kalibriert, wenn der Anteil positiver Ergebnisse unter Vorhersagen mit der angegebenen Wahrscheinlichkeit p gleich p ist — über viele Stichproben. Ein Modell, das 10.000 Mal 70 % sagt, sollte etwa 7.000 Mal recht haben. Kalibrierung ist eine von Diskriminierung getrennte Qualität: Ein Modell kann Gewinner von Verlierern korrekt sortieren und trotzdem falsche absolute Wahrscheinlichkeiten angeben — und ein solches Modell ist für Wetten nutzlos, weil Erwartungswertberechnungen korrekte Wahrscheinlichkeiten erfordern. Der Expected Calibration Error (ECE) ist das gebräuchlichste skalare Maß; Produktions-Wettmodelle zielen auf ECE unter 1,5 %.',
    related: ['catboost', 'expected-value', 'brier-score'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'closing-line-value',
    term: 'Closing Line Value (CLV)',
    shortDefinition:
      'Die Differenz zwischen der Quote, zu der eine Wette platziert wurde, und der Schlusskurs-Quote bei Anpfiff.',
    termCode: 'CLV',
    body:
      'Closing Line Value (CLV) misst, ob ein Wettspieler einen besseren Preis bekommt als der Markt bis zum Anpfiff berechnet. Wenn du zu 2,00 wettest und die Schlussquote 1,90 ist, hast du positiven CLV; der Markt hat sich gegen deine Seite bewegt, was ein starker Hinweis ist, dass du eine Kante vor schärferen Wettern erkannt hast. CLV gilt weithin als bester Frühindikator für langfristigen Wettgewinn, weil Schlussquoten den effizientesten Preis darstellen, den der Markt produziert. Positiver durchschnittlicher CLV über eine große Stichprobe impliziert fast immer positiven erwarteten ROI, auch wenn kurzfristige Ergebnisse aufgrund von Varianz negativ sind.',
    related: ['value-bet', 'expected-value'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'btts',
    term: 'Beide Mannschaften treffen (BTTS)',
    shortDefinition:
      'Ein Fußballmarkt, der mit Ja abrechnet, wenn beide Seiten mindestens ein Tor schießen, andernfalls mit Nein.',
    termCode: 'BTTS',
    body:
      'Beide Mannschaften treffen (BTTS) ist ein binärer Fußballmarkt, der mit Ja abrechnet, wenn beide Teams während der regulären Spielzeit mindestens ein Tor erzielen, andernfalls mit Nein. Er ist beliebt, weil ein einziges spätes Tor ein verlorenes Ticket noch umwandeln kann. Aus Modellierungsperspektive wird BTTS aus der gemeinsamen Verteilung von Heim- und Auswärtstoren abgeleitet: Unter einem Dixon-Coles bivariaten Poisson-Modell gilt P(BTTS=Ja) = 1 − P(HG=0) − P(AG=0) + P(HG=0, AG=0). BTTS-Grundraten liegen ligaweit typischerweise zwischen 48 und 58 %.',
    related: ['over-under-2-5', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
  {
    slug: 'over-under-2-5',
    term: 'Über/Unter 2,5 Tore',
    shortDefinition:
      'Ein Fußballmarkt, der mit Über abrechnet, wenn drei oder mehr Tore erzielt werden, und mit Unter bei zwei oder weniger.',
    body:
      'Über/Unter 2,5 Tore ist der weltweit meistgehandelte Fußball-Tore-Markt. Er rechnet mit Über ab, wenn drei oder mehr Tore in der regulären Spielzeit erzielt werden, und mit Unter bei zwei oder weniger; der halbe Torschnitt vermeidet Push-Ergebnisse. Wie BTTS wird es aus der gemeinsamen Torverteilung abgeleitet: Mit einem Dixon-Coles Poisson-Modell berechnet man P(Über 2,5) = 1 − P(Gesamttore ≤ 2). Liga-Grundraten variieren von etwa 47 % in defensiven Ligen bis 58 % in torerreichen Ligen wie der Bundesliga.',
    related: ['btts', 'poisson-model'],
    lastUpdated: LAST_UPDATED,
  },
];

export default entries;
