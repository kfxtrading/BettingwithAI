import type { LearnArticle } from './types';

const LAST_UPDATED = '2026-04-01';

const articles: Record<string, LearnArticle> = {
  'value-bets': {
    slug: 'value-bets',
    title: 'Value Bets im Fußball: Definition und wie man sie findet',
    description:
      'Eine Value Bet ist eine Wette, deren tatsächliche Gewinnwahrscheinlichkeit über der vom Buchmacher implizierten Wahrscheinlichkeit liegt. Hier erfährst du, wie du sie erkennst — mit Beispielen.',
    tldr:
      'Eine Value Bet liegt vor, wenn deine geschätzte Wahrscheinlichkeit höher ist als die margenbereinigte Marktwahrscheinlichkeit des Buchmachers. Der Erwartungswert ist positiv, auch wenn eine einzelne Wette verloren geht.',
    sections: [
      {
        heading: 'Definition',
        paragraphs: [
          'Eine Value Bet ist jede Wette, bei der (deine geschätzte Wahrscheinlichkeit) × (Dezimalquote) > 1 ist. Das Produkt heißt Erwartungswert (EV). Nur positiver EV zählt langfristig — das Ergebnis einer einzelnen Partie ist Rauschen.',
          'Die implizite Marktwahrscheinlichkeit ist 1 / Quote, doch rohe 1X2-Quoten enthalten 4–8 % Buchmachermarge. Diese Marge musst du zuerst entfernen, um fair zu vergleichen.',
        ],
      },
      {
        heading: 'So findest du Value Bets',
        paragraphs: [
          'Nutze ein Modell mit kalibrierten Wahrscheinlichkeiten für Heim, Unentschieden und Auswärts. Wandle alle drei Quoten in implizite Wahrscheinlichkeiten um, normiere sie auf Summe 1 und vergleiche mit dem Modell. Wo das Modell um mindestens 2–3 Prozentpunkte höher liegt, gibt es Value-Potenzial.',
          'Die Einsatzhöhe ist genauso wichtig wie das Erkennen einer Kante. Fraktionales Kelly (typisch 25–50 % von Voll-Kelly) maximiert das langfristige Wachstum, ohne dich in einer schwachen Woche zu ruinieren.',
        ],
      },
      {
        heading: 'Warum die meisten "Tipps" keine Value Bets sind',
        paragraphs: [
          'Affiliate-getriebene Tipp-Seiten wählen den wahrscheinlichsten Ausgang, nicht den am stärksten falsch bepreisten. Favoriten zu tippen hat nichts mit Value zu tun — ein Favorit zu Quote 1,20 mit 90 % wahrer Wahrscheinlichkeit hat EV 1,08; ein Außenseiter zu 4,50 mit 25 % wahrer Wahrscheinlichkeit hat EV 1,125. Der Außenseiter ist die Value Bet.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Sind Value Bets eine Gewinngarantie?',
        answer:
          'Nein. Value Bets sind im Erwartungswert positiv, nicht in jeder einzelnen Partie. Über 100 Wetten kann die Varianz erheblich sein; sinnvoll messbar wird es erst über mehrere Hundert.',
      },
      {
        question: 'Wie groß muss die Kante mindestens sein?',
        answer:
          'Die meisten Profis fordern ≥ 3–5 % Kante nach Berücksichtigung von Modellunsicherheit und Buchmachermarge, um Varianz und Ausführungskosten zu schlagen.',
      },
      {
        question: 'Warum bietet der Buchmacher überhaupt Value Bets an?',
        answer:
          'Buchmacher bepreisen für den Mediankunden. Soft Books reagieren langsam auf Verletzungen, Aufstellungen und scharfes Geld — diese Verzögerung ist der Quell von Value.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-01',
  },

  'implied-probability': {
    slug: 'implied-probability',
    title: 'Implizite Wahrscheinlichkeit aus Quoten: Formel und Margenabzug',
    description:
      'Wandle Dezimal-, Bruch- und amerikanische Quoten in implizite Wahrscheinlichkeiten um — und lerne, wie man die Buchmachermarge entfernt, damit die drei Ausgänge zu 100 % summieren.',
    tldr:
      'Implizite Wahrscheinlichkeit = 1 / Dezimalquote. Da die drei 1X2-Wahrscheinlichkeiten in der Summe über 100 % liegen (Overround), musst du jede durch die Gesamtsumme teilen, um die margenfreie Wahrscheinlichkeit zu erhalten.',
    sections: [
      {
        heading: 'Die Formel',
        paragraphs: [
          'Für Dezimalquoten: implizit = 1 / Quote. Quote 2,00 entspricht 50 %, Quote 4,00 entspricht 25 %.',
          'Für Bruchquoten (z. B. 5/2): implizit = Nenner / (Zähler + Nenner) = 2/7 ≈ 28,6 %.',
          'Für amerikanische Quoten: positiv (+150) → 100 / (150+100) = 40 %; negativ (-200) → 200 / (200+100) = 66,7 %.',
        ],
      },
      {
        heading: 'Margenabzug',
        paragraphs: [
          'Summiere die drei impliziten 1X2-Wahrscheinlichkeiten. Liegt die Summe bei 1,06, beträgt das Overround 6 %. Teile jede implizite Wahrscheinlichkeit durch 1,06 — das ist die "wahre" Schätzung des Buchmachers, die du mit deinem Modell vergleichst.',
          'Für Zwei-Wege-Märkte wie Über/Unter gilt dieselbe Logik — durch die Summe der beiden impliziten Wahrscheinlichkeiten teilen.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Wird die Marge immer gleichmäßig verteilt?',
        answer:
          'Nein. Buchmacher legen mehr Marge auf Favoriten oder Außenseiter, je nach Kundenbias. Proportionaler Abzug ist eine Näherung; bessere Methoden sind Shin und Power.',
      },
      {
        question: 'Warum wirkt meine margenfreie Wahrscheinlichkeit zu niedrig?',
        answer:
          'Weil rohe Quoten die Buchmacherüberzeugung immer um die Marge überzeichnen. Der Margenabzug zeigt die echte Markteinschätzung.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'kelly-criterion': {
    slug: 'kelly-criterion',
    title: 'Kelly-Kriterium für Sportwetten: Formel, Beispiele, Grenzen',
    description:
      'Das Kelly-Kriterium dimensioniert jede Wette so, dass das langfristige geometrische Wachstum maximiert wird. Hier sind Formel, Fußballbeispiel und Gründe für fraktionales Kelly.',
    tldr:
      'Kelly-Einsatz = (b·p − q) / b, mit b = Quote − 1, p deine Gewinnwahrscheinlichkeit und q = 1 − p. Profis nutzen meist nur ein Viertel oder die Hälfte davon, um Varianz zu kontrollieren.',
    sections: [
      {
        heading: 'Formel und ein Rechenbeispiel',
        paragraphs: [
          'Du schätzt Manchester City schlägt Arsenal mit Wahrscheinlichkeit 0,55. Quote 2,10 (b = 1,10). Kelly = (1,10 × 0,55 − 0,45) / 1,10 = 0,155 / 1,10 ≈ 14,1 % der Bankroll.',
          'Halb-Kelly würde 7 % setzen, Viertel-Kelly 3,5 %. Voll-Kelly ist mathematisch optimal nur, wenn deine Wahrscheinlichkeiten exakt sind — was sie nie sind.',
        ],
      },
      {
        heading: 'Warum fraktionales Kelly',
        paragraphs: [
          'Voll-Kelly ist brutal volatil: schon ein unverzerrter Schätzer mit realistischem Rauschen erzeugt 30–50 % Drawdowns. Fraktionales Kelly opfert ein wenig langfristige Rendite gegen deutlich kleinere Drawdowns — meist ein guter Tausch.',
          'Begrenze jede Einzelwette unabhängig von Kelly auf 1–3 % der Bankroll und meide Wetten mit negativem EV vollständig.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Was, wenn Kelly null oder negativ ist?',
        answer:
          'Nicht setzen. Negativer Kelly-Wert bedeutet, dass die Wette zu den angebotenen Quoten einen negativen Erwartungswert hat.',
      },
      {
        question: 'Funktioniert Kelly mit Kombiwetten?',
        answer:
          'Technisch ja, doch Kombi-Varianz ist so hoch, dass Kelly-Einsätze winzig werden. Die meisten Quants meiden Kombis, außer zur Absicherung.',
      },
      {
        question: 'Wie dimensioniere ich bei mehreren parallelen Wetten?',
        answer:
          'Nutze Simultan-Kelly: löse eine kleine Optimierung, die alle Wetten gemeinsam unter einer Gesamteinsatzgrenze dimensioniert. Oder wende Einzel-Kelly an und begrenze die Gesamtexposition auf 25–30 % der Bankroll.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'bankroll-management': {
    slug: 'bankroll-management',
    title: 'Bankroll-Management beim Fußballwetten: praktische Anleitung',
    description:
      'Bankroll-Management ist die Disziplin, Einsätze so zu wählen, dass du Varianz lange genug überstehst, um deine Kante wirken zu lassen. Hier sind die Regeln, die wirklich funktionieren.',
    tldr:
      'Behandle deine Bankroll als separaten, festen Pool. Riskiere 0,5–2 % pro Wette, jage keine Verluste, und überprüfe die Einsätze monatlich — nicht nach jedem Sieg oder Verlust.',
    sections: [
      {
        heading: 'Die fünf Regeln',
        paragraphs: [
          '1. Nur Geld einsetzen, dessen Verlust du dir leisten kannst. Niemals Miete, Ersparnisse oder geliehenes Geld.',
          '2. Standard 1 % der Bankroll pro Wette; fraktionales Kelly nur, wenn deine Wahrscheinlichkeiten kalibriert sind.',
          '3. Jede Wette protokollieren (Datum, Markt, Quote, Einsatz, Ergebnis, Modellwahrscheinlichkeit). Ohne Log keine Kante.',
          '4. Monatlich neu dimensionieren, nicht täglich. Aufwärtsdimensionieren nach einer heißen Woche ist die klassische Varianzfalle.',
          '5. Stop-Loss setzen (z. B. −25 % der Bankroll löst Modellreview aus) und Stop-Win (bei +50 % halbe Gewinne sichern).',
        ],
      },
    ],
    faqs: [
      {
        question: 'Wie groß sollte eine Start-Bankroll sein?',
        answer:
          'Ein Betrag, dessen Verlust dein Leben nicht beeinflusst. Viele ernsthafte Hobby-Wetter starten mit dem 100-fachen ihres üblichen Einsatzes.',
      },
      {
        question: 'Soll ich Gewinne auszahlen?',
        answer:
          'Ja, regelmäßig. Realisierte Gewinne fließen nie zurück. Viele Wetter zahlen 50 % jedes Monatsgewinns automatisch aus.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'closing-line-value': {
    slug: 'closing-line-value',
    title: 'Closing Line Value (CLV): bester Indikator für langfristigen ROI',
    description:
      'CLV misst, wie viel besser deine genommenen Quoten gegenüber den Quoten zum Anpfiff waren. Es ist der einzelne beste Frühindikator für Profitabilität.',
    tldr:
      'Closing Line Value (CLV) = (deine_Quote / Schlussquote) − 1. Konstant positiver CLV ist statistischer Beweis einer Kante — noch bevor Ergebnisse vorliegen.',
    sections: [
      {
        heading: 'Warum CLV kurzfristig wichtiger ist als ROI',
        paragraphs: [
          'ROI über 50 Wetten ist überwiegend Rauschen. CLV konvergiert viel schneller: 200 Wetten reichen oft, um einen mittleren CLV von +2 % als real zu bestätigen, während 200 Wetten ROI fast nichts beweisen.',
          'Sharps und Modellbauer werden in den ersten 6–12 Monaten nach CLV beurteilt. Ist der CLV positiv, folgt die Bankroll.',
        ],
      },
      {
        heading: 'Wie messen',
        paragraphs: [
          'Erfasse die Schlussquoten 1X2 (Pinnacle ist Goldstandard) und vergleiche mit deinen genommenen Quoten. Dein CLV ist positiv, wenn deine Quoten höher waren.',
          'Mittele den CLV pro Wette. Schon +1,5 % Durchschnitts-CLV nach Buchmachermarge signalisiert eine profitable Strategie bei sharpen Books.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Wo bekomme ich verlässliche Schlussquoten?',
        answer:
          'Pinnacle ist der De-facto-Referenzmarkt. Öffentliche Archive wie oddsportal.com und die football-data.co.uk-CSVs enthalten Schlussquoten zu Tausenden vergangener Spiele.',
      },
      {
        question: 'Kann eine Wette positiven CLV haben und trotzdem verlieren?',
        answer:
          'Natürlich — CLV misst Pricing-Skill, nicht Glück. Über Hunderte von Wetten übersetzt sich positiver CLV in positiven ROI; in einer einzelnen Partie ist das Ergebnis Rauschen.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'expected-goals-xg': {
    slug: 'expected-goals-xg',
    title: 'Expected Goals (xG) erklärt: Funktionsweise und Aussagekraft',
    description:
      'Expected Goals (xG) weist jedem Schuss eine Torwahrscheinlichkeit zu — basierend auf Position, Art und Kontext. Was xG misst, was nicht, und wie man es für Wetten nutzt.',
    tldr:
      'xG ist die Summe der Torwahrscheinlichkeiten pro Schuss. Über eine Saison ist Team-xG deutlich aussagekräftiger für künftige Ergebnisse als geschossene Tore — Varianz dominiert kurze Stichproben.',
    sections: [
      {
        heading: 'Welche Features ein xG-Modell nutzt',
        paragraphs: [
          'Jeder Schuss wird mit Merkmalen wie Distanz zum Tor, Winkel, Körperteil, Zuspielart (Steckpass vs. Flanke), Verteidigungsdruck und Spielstand bewertet. Das Modell liefert pro Schuss eine 0–1-Wahrscheinlichkeit.',
          'Das xG eines Teams pro Spiel ist die Summe dieser Wahrscheinlichkeiten. Über 38 Spiele ist eine Premier-League-Mannschaft mit +0,5 xG/Spiel über Liganschnitt nahezu sicher unter den Top sechs.',
        ],
      },
      {
        heading: 'Wie xG in der Spielprognose nutzen',
        paragraphs: [
          'Rollende 5–10-Spiele-xG-for und xG-against sind stärkere Features als reine Tordifferenz, weil sie Abschluss-Varianz und Torwart-Hot-Streaks herausnehmen.',
          'Kombiniere xG mit Schussqualität (xG pro Schuss), um Teams zu erkennen, die Chancen unterschiedlich erzeugen — Chance-Quality-Teams sind nachhaltiger als Chance-Quantity-Teams.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Ist xG besser als Tore?',
        answer:
          'Für Prognosen künftiger Spiele fast immer ja. Für die Beschreibung des Geschehenen gewinnen Tore — nur sie zählen in der Tabelle.',
      },
      {
        question: 'Warum widersprechen sich xG-Modelle?',
        answer:
          'Verschiedene Anbieter nutzen unterschiedliche Features und Trainingsdaten. Verwende konsistent ein Modell; relative Vergleiche sind wichtiger als Absolutwerte.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'btts-explained': {
    slug: 'btts-explained',
    title: 'Beide Teams treffen (BTTS): Strategie, Quoten und typische Fehler',
    description:
      'BTTS zahlt aus, wenn beide Mannschaften mindestens ein Tor erzielen. Wie der Markt bepreist, wann er falsch liegt und worauf in Teamprofilen zu achten ist.',
    tldr:
      'BTTS Ja ist profitabel, wenn zwei offensive Teams mit anfälligen Defensiven aufeinandertreffen — typische Quoten 1,65–1,90. Pures xG ist ein starker Prädiktor; reine Abschluss-Varianz nicht.',
    sections: [
      {
        heading: 'Wann BTTS Ja Value hat',
        paragraphs: [
          'Suche nach Teams, die jeweils ≥ 1,3 xG-for und ≥ 1,0 xG-against pro Spiel über die letzten 10 Partien generieren. Mittelfeld- bis Mittelfeld-Offensiv-Teams überliefern historisch gut auf BTTS.',
          'Vermeide BTTS Ja bei Spielen mit Elite-Defensiven und starken Torhütern — sie produzieren zu viele "Zu-Null"-Ergebnisse.',
        ],
      },
      {
        heading: 'BTTS Nein: das kontrarische Spiel',
        paragraphs: [
          'BTTS Nein ist unterbewertet bei klarem Favorit + defensiv schwachem Außenseiter: der Favorit gewinnt oft zu null. Liga-Mittelwerte helfen: Serie A hat historisch höhere BTTS-Nein-Raten als die Bundesliga.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Was bedeutet "BTTS Ja & Über 2,5"?',
        answer:
          'Ein kombinierter Markt: beide Teams müssen treffen UND die Toranzahl ≥ 3. Anspruchsvoller, mit längeren Quoten.',
      },
      {
        question: 'Ist BTTS leichter zu prognostizieren als 1X2?',
        answer:
          'Es ist ein binärer Ausgang, also einfacher zu kalibrieren. Aber die Marge auf BTTS ist oft höher als auf 1X2 — die Kante pro Wette ist meist kleiner.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'over-under-2-5': {
    slug: 'over-under-2-5',
    title: 'Über/Unter 2,5 Tore: Wie der Markt funktioniert und wie man ihn schlägt',
    description:
      'Über 2,5 zahlt bei 3+ Toren. So prognostizierst du Torsummen über xG, Liga-Kontext und Tempo-Signale.',
    tldr:
      'Über/Unter 2,5 wird an der 3-Tore-Schwelle abgerechnet. Prognostiziere aus kombiniertem xG-for + Gegner-xG-against, Liga-Schnitt und Heim/Auswärts-Effekten.',
    sections: [
      {
        heading: 'Modellierung der Torsumme',
        paragraphs: [
          'Ein einfaches Poisson-Modell nutzt die erwarteten Tore beider Teams + Gegnerische Gegentore, angepasst an den Liga-Schnitt. Kombinierte erwartete Tore von ≥ 2,7 stützen ein Über-2,5-Lean bei fairen Quoten.',
          'Dixon-Coles verfeinert Poisson, indem es Korrelationen niedriger Ergebnisse (0-0, 1-0, 0-1, 1-1) korrigiert — Standard in der Fußballmodellierung seit 1997.',
        ],
      },
      {
        heading: 'Häufige Fehler',
        paragraphs: [
          'Recency Bias ist der Killer. Ein 4:0 im letzten Spiel drückt Gelegenheitsspieler in Richtung Über; das Modell sollte sich kaum bewegen, weil sich erwartete Tore kaum ändern.',
          'Wetter und Pitch-Bedingungen im Winter ignorieren — schwerer Boden oder starker Wind senken die Torgrenze zuverlässig.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Wie hoch ist die Über-2,5-Quote langfristig?',
        answer:
          'Über die Top-5-Ligen liegt sie bei rund 53–55 %. Bei typischer Quote 1,85 braucht der Breakeven 54,1 % — ein enger Markt.',
      },
      {
        question: 'Was ist Asian Handicap auf Über 2,5?',
        answer:
          'Asian-Total-Märkte verschieben die Linie um 0,25 oder 0,5, um Push-Resultate zu vermeiden. Über 2,75 splittet den Einsatz zwischen Über 2,5 und Über 3,0.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  '1x2-explained': {
    slug: '1x2-explained',
    title: '1X2-Wette erklärt: der liquideste Fußballmarkt',
    description:
      '1X2 ist eine Drei-Wege-Wette auf Heimsieg (1), Unentschieden (X) oder Auswärtssieg (2). Wie er bepreist wird, warum Margen variieren und wo Value liegt.',
    tldr:
      '1X2 ist der tiefste, liquideste Fußballmarkt. Die drei impliziten Wahrscheinlichkeiten summieren sich zu 104–108 % — das Overround. Nach Margenabzug ergibt sich die wahre Markteinschätzung.',
    sections: [
      {
        heading: 'Wie der Markt bepreist wird',
        paragraphs: [
          'Sharpe Books wie Pinnacle bepreisen 1X2 mit 100,5–101 % (sub-2 % Marge). Recreational Books tragen 5–8 % Marge. Vergleiche immer mehrere Books vor einer Wette.',
          'Unentschieden sind systematisch schwerer zu prognostizieren als Siege — die implizite Draw-Wahrscheinlichkeit liegt typisch im engen Band 22–28 %, daher liegen die meisten Kanten auf H- oder A-Seite.',
        ],
      },
      {
        heading: 'Wo 1X2-Value lebt',
        paragraphs: [
          'Marktüberreaktionen auf jüngste Ergebnisse (4:0-Siege, Derby-Niederlagen) bei kleinen Stichproben. Modelle, die kurzfristiges Rauschen ignorieren, schlagen menschlich gesetzte Linien hier konstant.',
          'Spiele am Saisonende ohne sportliche Bedeutung — Public Money überbelohnt das noch motivierte Team.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Was ist "1N2" auf französischen Wett-Sites?',
        answer:
          'Identisch mit 1X2: 1 = Heimsieg, N = Nul (Unentschieden), 2 = Auswärtssieg. Nur Notation, kein Unterschied.',
      },
      {
        question: 'Soll ich auf das Unentschieden setzen?',
        answer:
          'Nur, wenn deine kalibrierte Wahrscheinlichkeit über der impliziten liegt. In engen Spielen ist das Unentschieden coin-flip-ähnlich; viele Modelle passen schlicht.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'model-accuracy-brier-calibration': {
    slug: 'model-accuracy-brier-calibration',
    title: 'Wie man Fußball-Prognosemodelle bewertet: Brier, RPS und Kalibrierung',
    description:
      'Trefferquote ist eine schlechte Metrik für Wahrscheinlichkeitsmodelle. Brier-Score, RPS und Reliability-Diagramme zeigen, ob ein Modell wirklich kalibriert ist.',
    tldr:
      'Nutze Brier-Score und Ranked Probability Score (RPS) zum Vergleich, sowie ein Reliability-Diagramm, um zu prüfen, ob "70 %"-Tipps tatsächlich in 70 % der Fälle gewinnen.',
    sections: [
      {
        heading: 'Warum Trefferquote irreführt',
        paragraphs: [
          'Ein Modell, das immer den Favoriten wählt, erreicht ~52 % Trefferquote in der Premier League — bietet aber null Kante über den Buchmacher. Trefferquote prüft nur das Argmax, nicht die Wahrscheinlichkeiten.',
        ],
      },
      {
        heading: 'Brier-Score und RPS',
        paragraphs: [
          'Brier = mittlerer quadratischer Fehler zwischen Wahrscheinlichkeitsvektor und One-Hot-Ergebnis. Niedriger ist besser.',
          'RPS (Ranked Probability Score) ist Briers ordinaler Cousin: er bestraft konfidente Fehlprognosen auf benachbarten Ausgängen härter — der De-facto-Standard für 1X2.',
        ],
      },
      {
        heading: 'Reliability-Diagramme',
        paragraphs: [
          'Bilde alle prognostizierten Wahrscheinlichkeiten in z. B. 10 Bins ab. Plot der prognostizierten Wahrscheinlichkeit pro Bin gegen die tatsächliche Trefferrate. Ein perfekt kalibriertes Modell liegt auf der Diagonalen.',
          'Wir veröffentlichen das Reliability-Diagramm der Live-Vorhersagen unter /performance.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Was ist eine gute RPS-Bandbreite für 1X2 im Fußball?',
        answer:
          'Top-5-Ligen liegen bei 0,19–0,21 für gut kalibrierte Modelle. Unter 0,20 ist sehr stark; über 0,22 deutet auf Kalibrierungsprobleme.',
      },
      {
        question: 'Warum nicht einfach Log-Loss?',
        answer:
          'Log-Loss bestraft konfidente Fehlprognosen unendlich. Brier ist robuster gegen seltene Volltreffer; RPS respektiert die Ordinalstruktur von H/D/A.',
      },
    ],
    lastUpdated: LAST_UPDATED,
  },

  'catboost-vs-xgboost': {
    slug: 'catboost-vs-xgboost',
    title: 'CatBoost vs. XGBoost für Fußballvorhersagen: Ein Praxisvergleich',
    description:
      'Ein direkter Vergleich von CatBoost und XGBoost für 1X2-Fußballvorhersagen — Kategorienbehandlung, Trainingsgeschwindigkeit, Kalibrierung, RPS und wann welche Bibliothek zu wählen ist.',
    tldr:
      'Beide Bibliotheken erreichen nahezu identische Vorhersagegenauigkeit auf tabellarischen Fußballdaten. CatBoost gewinnt bei Out-of-the-box-Kategorienbehandlung und Kalibrierung; XGBoost bei Trainingsgeschwindigkeit auf dichten numerischen Features. Für 1X2 mit 70+ gemischten Features ist CatBoost die sicherere Wahl.',
    sections: [
      {
        heading: 'Unterschiede unter der Haube',
        paragraphs: [
          'XGBoost verwendet level-weises Baumwachstum mit Second-Order-Gradient-Boosting. Kategorische Features müssen manuell kodiert werden (One-Hot, Label-Encoding oder Target-Encoding).',
          'CatBoost verwendet symmetrische (oblivious) Bäume und ein ordered-Boosting-Schema, das Target-Leakage beim automatischen Target-Encoding von kategorischen Features verhindert. Das macht CatBoost robuster mit Standard-Hyperparametern.',
        ],
      },
      {
        heading: 'Empirischer Vergleich auf 1X2-Fußballdaten',
        paragraphs: [
          'Auf unserem Top-5-Ligen-Feature-Set (70+ Features, 5 Trainingssaisons, Walk-Forward-Backtest) unterscheiden sich CatBoost und XGBoost bei korrekter Abstimmung um weniger als 0,005 RPS. Standard-Hyperparameter bevorzugen CatBoost um ~0,01 RPS.',
          'Bei der Kalibrierung hat CatBoost einen messbaren Vorsprung: ECE vor isotonischer Post-Kalibrierung beträgt ~2,4 % (CatBoost) vs. ~3,1 % (XGBoost). Nach Isotonic-Kalibrierung liegen beide unter 1,5 %.',
        ],
      },
      {
        heading: 'Wann CatBoost wählen',
        paragraphs: [
          'Viele hochkardinalitäts-kategorische Features (Team-IDs, Schiedsrichter-IDs, Spielstätten). CatBoost kodiert sie sicher ohne Leakage.',
          'Du willst starke Out-of-the-box-Kalibrierung und wenig Zeit zum Tunen. Die Defaults sind fehlerverzeihend.',
        ],
      },
      {
        heading: 'Wann XGBoost wählen',
        paragraphs: [
          'Deine Features sind überwiegend dichte Zahlen und du hast kategorische Features bereits sorgfältig kodiert.',
          'Du brauchst die absolute schnellste Trainingszeit auf CPU.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Sollte ich stattdessen LightGBM verwenden?',
        answer:
          'LightGBM ist konkurrenzfähig und schneller als XGBoost auf großen Datasets. Für < 1 Mio. Zeilen Fußballdaten ist der Geschwindigkeitsvorteil meist unwesentlich; die Kalibrierung ist der wichtigere Unterschied, und CatBoost gewinnt dort noch immer.',
      },
      {
        question: 'Schlägt ein Ensemble aus beiden ein Einzelmodell?',
        answer:
          'Ja, geringfügig. Ein 50/50-Durchschnitt kalibrierter CatBoost- und XGBoost-Wahrscheinlichkeiten reduziert RPS typischerweise um weitere 0,001–0,003 gegenüber dem besten Einzelmodell.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },

  'pi-ratings-explained': {
    slug: 'pi-ratings-explained',
    title: 'Pi-Ratings erklärt: Das Fußball-Bewertungssystem hinter modernen Modellen',
    description:
      'Pi-Ratings (Constantinou & Fenton, 2013) sind das ortsbasierte Fußball-Bewertungssystem, das in vielen modernen Vorhersagemodellen eingesetzt wird. Dieser Leitfaden erklärt die Update-Regel, zeigt ein konkretes Beispiel und erklärt, wie Pi-Ratings als Modell-Features genutzt werden.',
    tldr:
      'Pi-Ratings geben jedem Team eine separate Heim- und Auswärtsstärke, die nach jedem Spiel durch einen gewichteten Fehlerterm aktualisiert wird. Sie schlagen reine Tabellenposition und Elo bei Out-of-Sample-1X2-Vorhersagen um 1–2 % Genauigkeit – bei null Implementierungsaufwand.',
    sections: [
      {
        heading: 'Was Pi-Ratings sind',
        paragraphs: [
          'Pi-Ratings, eingeführt von Anthony Costa Constantinou und Norman E. Fenton (2013), weisen jedem Team zwei Ratings zu: eine Heimstärke R_H und eine Auswärtsstärke R_A.',
          'Die Zweiteilung macht Pi-Ratings besonders geeignet für Fußball. Der Heimvorteil ist groß (≈ 0,3 Tore in den Top-5-Ligen) und teamspezifisch — Atalanta war historisch ein deutlich stärkeres Heimteam als Auswärtsteam; Brighton das Gegenteil.',
        ],
      },
      {
        heading: 'Die Update-Regel',
        paragraphs: [
          'Vor dem Anpfiff ist das prognostizierte Torquotienten-Delta: gd_pred = R_H(Heim) − R_A(Auswärts).',
          'Nach dem Spiel mit tatsächlichem Torverhältnis gd_actual ist der Fehler e = gd_actual − gd_pred. Die Dämpfungsfunktion ψ(e) = sign(e) · 3 · log10(1 + |e|) verhindert, dass hohe Niederlagen dominieren.',
          'Beide Teams aktualisieren beide Ratings, mit separaten Lernraten λ für die gespielte Seite und γ für die andere (typisch: λ ≈ 0,06, γ ≈ 0,5·λ).',
        ],
      },
      {
        heading: 'Pi-Ratings als Modell-Features nutzen',
        paragraphs: [
          'Direkte Features: R_H_home, R_H_away, R_A_home, R_A_away sowie deren Deltas und das prognostizierte Torquotienten-Delta. Diese fünf abgeleiteten Features allein erreichen ~52–54 % Genauigkeit bei 1X2.',
          'Besser: sie in ein Poisson-Modell einspeisen. R_diff in erwartete Heim- und Auswärtstore übersetzen und mit der Skellam-Verteilung 1X2-Wahrscheinlichkeiten ableiten.',
          'Noch besser: als Features in einem CatBoost/XGBoost/MLP-Ensemble zusammen mit xG, Ruhepausen und Form verwenden.',
        ],
      },
    ],
    faqs: [
      {
        question: 'Sind Pi-Ratings besser als Elo für Fußball?',
        answer:
          'Ja, leicht. Die Heim-/Auswärts-Aufteilung erfasst ortsspezifische Stärke, die reines Elo nicht kann. Beide werden von vollständigen feature-basierten ML-Modellen übertroffen, aber Pi-Ratings bleiben ein Top-3-Einzelfeature in jedem 1X2-Modell.',
      },
      {
        question: 'Welche Lernrate sollte ich verwenden?',
        answer:
          'Das ursprüngliche Paper verwendete λ ≈ 0,06 und γ = 0,5·λ. Wir empfehlen ein Grid-Search über λ ∈ {0,04, 0,05, 0,06, 0,07, 0,08} auf einer Hold-out-Saison, optimiert auf RPS oder Log-Loss.',
      },
    ],
    lastUpdated: LAST_UPDATED,
    datePublished: '2026-04-25',
  },
};

export default articles;
