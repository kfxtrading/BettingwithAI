# Plan — Support-Chat Upgrade: Follow-up-Fragen + Formulierungs-Cluster

## Ziel
Zwei neue Fähigkeiten im Support-Chatbot, ohne die bestehende 5-Suggestion-UI zu
brechen:

1. **Follow-up-Fragen.** Nach jeder Bot-Antwort wird **genau eine** thematische
   Anschlussfrage als klickbarer Chip angeboten. Klick → die Folgefrage wird
   gestellt und beantwortet (eigene, neue Antwort, nicht dieselbe wie die
   Hauptantwort).
2. **Formulierungs-Cluster.** Alternative Nutzerformulierungen („Variationen")
   pro Intent — echter handgeschriebener Text, ergänzend zur bestehenden
   Template-Paraphrase-Augmentation, um die Fuse.js-Trefferquote auf
   idiomatische Anfragen („Hat diese Wette positiven Erwartungswert?",
   „Wie finde ich einen guten Tipp?") zu heben.

Quelle: Report mit **128 Hauptfrage→Folgefrage-Paaren** (8 Kapitel) +
**4 Beispiel-Clustern** mit je 5 Variationen + gemeinsamer Folgefrage.

---

## Datenmodell-Erweiterung

### `web/lib/faq.ts` — `FaqEntry` bekommt optionale Felder
```ts
export interface FaqEntry {
  id: string;
  questionKey: DictionaryKey;
  answerKey: DictionaryKey;
  tags: string[];
  /** id of another FaqEntry that represents the natural follow-up. */
  followUpId?: string;
  /** additional localized question strings the user might type (same intent). */
  altQuestionKeys?: DictionaryKey[];
}
```

- **`followUpId`** zeigt auf einen regulären `FaqEntry` (kein Spezialtyp) →
  Follow-up ist voll suchbar, voll übersetzt, ML-exportierbar.
- **`altQuestionKeys`** sind zusätzliche Übersetzungskeys. `buildFuse` indexiert
  die Texte als zusätzliche `question`-ähnliche Felder, damit Fuse sie findet,
  ohne dass jede Variante eine eigene Intent-Klasse wird.

### Neue Translation-Keys
Pro Kapitel-Slug der Hauptfrage bekommen wir:

| Typ | Key-Schema | Anzahl |
|---|---|---|
| Folgefrage-Frage | `support.faq.<chapter>.<slug>.fq` | 128 |
| Folgefrage-Antwort | `support.faq.<chapter>.<slug>.fa` | 128 |
| Cluster-Variationen | `support.faq.<chapter>.<slug>.alt1..alt5` | 4 × 5 = 20 (Start-Set) |

→ **276 neue DictionaryKey-Literale × 5 Locales = 1.380 neue Dictionary-Strings**.
Folgefrage-Antworten werden **neu formuliert** (unterscheiden sich inhaltlich
von der Hauptantwort, 2–4 Sätze, gleicher neutraler Ton).

### Neue `FaqEntry`-Einträge (Follow-ups als eigenständige Intents)
Für jede der 128 Folgefragen ein neuer Eintrag, angehängt **nach** den
bestehenden 134 Einträgen, damit `FAQ_ENTRIES.slice(0, 5)` unverändert die
ersten 5 Originale zeigt:

```ts
{
  id: 'basics-1x2-fu',
  questionKey: 'support.faq.basics.oneX2.fq',
  answerKey:   'support.faq.basics.oneX2.fa',
  tags: ['1x2','double chance','when','wann','sinnvoll'],  // geerbt + Follow-up-Keywords
},
```

Das Parent-Entry `basics-1x2` wird um `followUpId: 'basics-1x2-fu'` erweitert.

**Ergebnis:** `FAQ_ENTRIES` wächst von 134 → **262** Einträge
(134 Originale + 128 Follow-ups). Startup-Suggestions bleiben Index 0–4 =
`valueBet, accuracy, dataSource, snapshotUpdate, kelly`.

---

## Betroffene Dateien (in Reihenfolge)

| Datei | Änderung | Umfang |
|---|---|---|
| `web/lib/faq.ts` | `FaqEntry` + 128 Follow-up-Entries + `followUpId`/`altQuestionKeys` an Parents | +~900 Zeilen |
| `web/lib/i18n/en.ts` | 276 neue Literale in `DictionaryKey`-Union + Dictionary-Map | +~580 Zeilen |
| `web/lib/i18n/de.ts` | Primärtexte (Quelle) — 276 Keys | +~580 Zeilen |
| `web/lib/i18n/es.ts` | Übersetzungen 276 Keys | +~580 Zeilen |
| `web/lib/i18n/fr.ts` | Übersetzungen 276 Keys | +~580 Zeilen |
| `web/lib/i18n/it.ts` | Übersetzungen 276 Keys | +~580 Zeilen |
| `web/lib/faq.ts` (`buildFuse`) | `altQuestionKeys` in `SearchableEntry` indexieren | +~15 Zeilen |
| `web/components/SupportChat.tsx` | Follow-up-Chip nach Bot-Antwort | +~40 Zeilen |
| `scripts/export_support_faq.py` | Kapitel-Detection robust bei `.fq`/`.fa`-Suffix | +~8 Zeilen |
| `scripts/augment_support_faq.py` | `altQuestionKeys` als zusätzliche Paraphrase-Seeds lesen | +~20 Zeilen |

---

## UI-Änderung (`SupportChat.tsx`)

**`Message`-Typ erweitern**, damit wir wissen, welche Folgefrage zu einer
gerade gezeigten Antwort gehört:

```ts
type Message =
  | { role: 'user'; text: string }
  | { role: 'bot'; text: string; followUpEntryId?: string };
```

In `handleAsk`: wenn `top.score ≤ HIGH_CONFIDENCE` (z. B. 0.4) UND
`top.entry.followUpId` vorhanden → den `followUpEntryId` auf der Bot-Message
speichern.

Render-Logik: unter der **letzten** Bot-Message (wenn sie eine `followUpEntryId`
hat und noch nicht angeklickt wurde), einen Chip mit dem Fragetext rendern.
Style = Kopie der bestehenden `suggestions`-Buttons. onClick →
`handleAsk(t(followUpEntry.questionKey))`.

Pseudocode:
```tsx
{lastBotMsg?.followUpEntryId && (
  <button
    type="button"
    onClick={() => {
      const fu = byId.get(lastBotMsg.followUpEntryId);
      if (fu) handleAsk(t(fu.questionKey));
    }}
    className="…bestehende suggestion-Styles…"
  >
    ↳ {t(byId.get(lastBotMsg.followUpEntryId).questionKey)}
  </button>
)}
```

Keine weitere State-Maschine, keine Dialog-Trees. Die Follow-up-Kette
entsteht natürlich: das Follow-up-Entry kann selbst wieder eine
`followUpId` haben (optional, zunächst nicht gesetzt).

---

## Suchindex-Erweiterung (`buildFuse`)

```ts
const searchable: SearchableEntry[] = FAQ_ENTRIES.map((e) => {
  const altQuestions = (e.altQuestionKeys ?? []).map(t);
  return {
    id: e.id,
    question: t(e.questionKey),
    questionNorm: normalizeText(t(e.questionKey)),
    altQuestions,                                             // NEW
    altQuestionsNorm: altQuestions.map(normalizeText),        // NEW
    tags: e.tags,
    tagsNorm: e.tags.map(normalizeText).filter(Boolean),
  };
});
```

Fuse-Keys erweitert:
```ts
keys: [
  { name: 'question',         weight: 0.30 },
  { name: 'questionNorm',     weight: 0.25 },
  { name: 'altQuestions',     weight: 0.15 },
  { name: 'altQuestionsNorm', weight: 0.15 },
  { name: 'tags',             weight: 0.075 },
  { name: 'tagsNorm',         weight: 0.075 },
]
```

Tag-Vokabular + Reverse-Index schlucken `altQuestions` automatisch, da sie
beim Vokabel-Build mitgeliefert werden.

---

## Inhaltliche Guidelines

### Folgefrage-Antwort
- 2–4 Sätze, dieselbe neutrale Tonalität wie bestehende Antworten
- **Muss sich inhaltlich unterscheiden** von der Hauptantwort (sonst sinnlos)
- Konkret & spezifisch — die Folgefrage ist meist „ein Level tiefer"
  (Beispiel: Main = „Was ist BTTS?" → Antwort definiert; Follow-up = „Welche
  Statistiken sprechen stark für BTTS?" → Antwort listet 2-3 konkrete KPIs
  wie xG-Trends, PPDA, Clean-Sheet-Rate)
- Bei sensiblen Kapiteln (4 Fehler, 7 Profit): klarer Hinweis auf Risiko /
  verantwortungsvolles Spielen beibehalten

### Variationen (`altQuestionKeys`)
- 5 handgeschriebene Alternativformulierungen pro Intent (aus Report übernommen,
  4 Cluster × 5 = 20 zum Start, später erweiterbar ohne Schema-Änderung)
- Pro Sprache eigene Übersetzung — **keine** Template-Paraphrase (dafür gibt es
  bereits `augment_support_faq.py`)
- Ziel: idiomatische Ausdrücke, die Fuse.js bisher nicht zuverlässig findet

### Tag-Ableitung für Follow-ups
Regel: Tags des Parent-Entries **erben** + 2–3 Keywords aus der Folgefrage
hinzufügen (mehrsprachig DE+EN). Beispiel:
- Parent `basics-1x2`: `['1x2','markt','heim','auswärts','draw','home','away']`
- Follow-up `basics-1x2-fu` („Wann ist 1X2 sinnvoller als Double Chance?"):
  `['1x2','double chance','wann','when','sinnvoll','vergleich','comparison']`

---

## Generierungs-Strategie

Ähnlich zum bestehenden Muster:

1. **Python-Generator-Script** `scripts/_gen_followup_faq.py` (temporär,
   nach Ausführung löschen):
   - Liest den 316-Zeilen-Report als tupellistencode
   - Patcht die 6 Zieldateien mit Sentinel-Markern
     (`// <END_FOLLOWUPS>`, `// <END_ALT_VARIATIONS>`)
   - Quellentext = DE, Antworten frisch formuliert
   - Übersetzungen EN/ES/FR/IT: regelbasierte Stubs + manuelle Glossar-Map
     für wettspezifische Termini (Value Bet, Overround, BTTS, xG, CLV, …)

2. **Manuelle Nacharbeit**: nach Generator-Run die Übersetzungen auf
   Natürlichkeit prüfen (Fachbegriffe sollten konsistent bleiben; Glossar
   im Generator hardcoden).

3. **Verifikation**:
   - `cd web && npm run type-check` — strikte DictionaryKey-Union prüft
     Vollständigkeit aller 5 Locales
   - `cd web && npm run lint`
   - `python scripts/export_support_faq.py` — erwartet **262 intents ×
     5 langs = 1.310 rows** in `dataset.jsonl` (von aktuell 670)
   - `python scripts/augment_support_faq.py` — erwartet ~25.000 paraphrase
     rows (fast 2× vorher)
   - Smoke-Test `npm run dev`, Support-Chat:
     a. Startup zeigt weiterhin 5 Originale
     b. Frage „was ist 1x2" → Antwort + Chip „Wann ist 1X2 sinnvoller als
        Double Chance?"
     c. Chip-Klick → Folgefrage-Antwort erscheint
     d. Frage „Hat diese Wette positiven Erwartungswert?" → matcht
        `value-bet` via `altQuestionKeys`
     e. Sprachwechsel EN/ES/FR/IT → alle Folgefragen + Varianten übersetzt

---

## Risiken & Gegenmaßnahmen

| Risiko | Maßnahme |
|---|---|
| Bundle wächst ~200 KB | Akzeptabel; Dictionary bereits ~60 KB/Locale. Ggf. Code-Splitting des Supports (dynamic import `SupportChat`). |
| Falsche Folgefrage erscheint bei Low-Confidence-Match | Chip nur zeigen, wenn `score ≤ 0.4` (Hochkonfidenz-Gate). |
| Follow-up-Antwort wiederholt nur Hauptantwort (schlechte UX) | Content-Guideline: Follow-up muss „eine Ebene tiefer" sein; Review pro Eintrag. |
| Fuse-Threshold 0.45 wird mit 262 Entries zu lax | Bei der Verifikation messen; fallback: auf 0.40 senken. |
| ML-Pipeline rechnet Follow-ups als eigene Klassen | Gewollt — Follow-ups sind separate Intents. `intents.json` wächst auf 262 Klassen (immer noch trainierbar mit ~5k Originalen × Augmentation). |
| Keys-Kollision `oneX2` vs. reserved word `1x2` (führende Ziffer nicht JS-konform) | Alle Slugs als JS-kompatibler camelCase (`oneX2`, `overUnder25`, `btts`, …). Bereits aktueller Konvention in `faq.ts`. |

---

## Kritische Dateien (für die Ausführung)

- `web/lib/faq.ts` — Datenmodell + Entries
- `web/lib/i18n/{en,de,es,fr,it}.ts` — Übersetzungen + DictionaryKey-Union
- `web/components/SupportChat.tsx` — Follow-up-Chip-Rendering
- `web/lib/faqNormalize.ts` — unverändert (Normalisierung deckt alles ab)
- `scripts/export_support_faq.py` — Parser muss `.fq`/`.fa`-Suffixe akzeptieren
- `scripts/augment_support_faq.py` — `altQuestionKeys` als Seed-Input

---

## Verifikationsplan (End-to-End)

```bash
# 1) Typen & Lint
cd web && npm run type-check && npm run lint

# 2) Dataset re-export — erwartet n_intents = 262, n_rows = 1310
cd .. && python scripts/export_support_faq.py
python -c "import json; d=json.load(open('data/support_faq/stats.json')); assert d['n_intents']==262 and d['n_rows']==1310, d; print('OK')"

# 3) Augmentation — erwartet n_output_rows ~ 25.000
python scripts/augment_support_faq.py

# 4) UI smoke test
cd web && npm run dev
# → Chat öffnen:
#    a) 5 Startvorschläge sichtbar (unverändert)
#    b) „was ist 1x2" → Antwort + Follow-up-Chip erscheint
#    c) Chip-Klick → neue Antwort erscheint
#    d) „hat diese wette positiven erwartungswert" → Treffer auf value-bet
#    e) Locale-Switch auf EN/ES/FR/IT → Chip-Text übersetzt

# 5) Commit
git add -A
git commit -m "feat:add-follow-up-questions-and-phrasing-clusters-to-support-FAQ"
```

---

## Zusammenfassung

| Metrik | Vorher | Nachher |
|---|---|---|
| Intents | 134 | **262** |
| Dataset-Zeilen (Originale × 5 langs) | 670 | **1.310** |
| Augmentierte Zeilen | 13.253 | **~25.000** |
| Translation-Keys pro Locale | ~268 | **~544** |
| Fuse-Searchable-Felder | 4 | **6** (+ altQuestions, altQuestionsNorm) |
| UI-Änderung | keine | +1 Follow-up-Chip unter letzter Bot-Message |
| Startup-Suggestions | 5 Originale | **5 Originale (unverändert)** |

Das Feature ist additiv: kein bestehender Flow bricht, alle neuen Pfade sind
opt-in über `followUpId` und `altQuestionKeys`. ML-Pipeline skaliert linear.
