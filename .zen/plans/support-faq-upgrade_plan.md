# Plan: Internal Support-Chat FAQ Upgrade (124 neue Fragen/Antworten)

## Ziel
Interne Logik des Support-Chatbots (`SupportChat.tsx`) mit ~124 zusätzlichen
Fragen/Antworten aus der Nutzerliste erweitern, sodass die Fuse.js-Suche diese
Matches findet. **Keine UI-Änderung** — die Anzeige der 5 Startvorschläge
(`FAQ_ENTRIES.slice(0, SUGGESTION_LIMIT)`) bleibt unverändert; die neuen
Einträge werden hinter Index 5 angehängt und sind nur über Sucheingaben
erreichbar.

## Betroffene Dateien
- `web/lib/faq.ts` — 124 neue Einträge an `FAQ_ENTRIES` anhängen (id, questionKey, answerKey, tags).
- `web/lib/i18n/en.ts` — 248 neue `DictionaryKey`-Literale (2 pro Frage: `.q`, `.a`) in der Union ergänzen und in der EN-Dictionary-Map mit englischen Übersetzungen befüllen.
- `web/lib/i18n/de.ts` — Deutsche Antworten (Primärsprache der Quelle).
- `web/lib/i18n/es.ts`, `fr.ts`, `it.ts` — Übersetzungen mitliefern (strict TS erzwingt alle Keys).

**Keine** Änderungen an `SupportChat.tsx` nötig — die Komponente liest
`FAQ_ENTRIES` + nutzt Fuse.js über alle Einträge, und die
`slice(0, 5)`-Vorschläge bleiben automatisch die 10 bestehenden.

## ID-Namensschema
Gruppierung nach den 8 Kapiteln der Quelldatei:

| Kapitel | Prefix | Anzahl |
|---|---|---|
| 1. Grundlagen | `basics.*` | 20 |
| 2. Fußball-Analyse | `analysis.*` | 20 |
| 3. Strategien & Systeme | `strategy.*` | 20 |
| 4. Häufige Fehler | `mistakes.*` | 10 |
| 5. KI & Daten | `ai.*` | 20 |
| 6. Quoten & Markt | `market.*` | 10 |
| 7. Profit & Realität | `profit.*` | 10 |
| 8. Plattform & Produkt | `platform.*` | 14 |
| **Summe** | | **124** |

Beispiel: Id `basics-1x2`; Keys `support.faq.basics.1x2.q` / `.a`.

## Datenformat (pro Eintrag)
```ts
{
  id: 'basics-1x2',
  questionKey: 'support.faq.basics.1x2.q',
  answerKey:   'support.faq.basics.1x2.a',
  tags: ['1x2', 'markt', 'heim', 'auswärts', 'unentschieden', 'draw', 'home', 'away'],
}
```
Tags enthalten relevante deutsche + englische Schlüsselwörter, damit Fuse.js
sprachübergreifend gut matcht.

## Antwort-Guideline
- 2–4 Sätze, direkt & neutral (wie vorhandene 10 FAQ-Einträge).
- Kein Werbeton, keine Glücksspiel-Anreize.
- Bei sensiblen Themen (Kap. 4 „Fehler", Kap. 7 „Profit") klarer Hinweis auf
  verantwortungsvolles Spielen — passt zur `support.faq.responsible.a`-Tonalität.
- Bei Plattform-Fragen (Kap. 8) auf die eigene App-Architektur referenzieren
  (Snapshot, API, Konfidenz, Value Bets).

## Implementierungsschritte
1. **`faq.ts`**: Unter den 10 bestehenden Einträgen die 124 neuen anhängen
   (Reihenfolge egal — Vorschläge kommen aus Index 0–4).
2. **`en.ts`**:
   - Im `DictionaryKey`-Union-Type 248 neue Literale am Ende der
     `'support.faq.*'`-Block-Liste ergänzen.
   - In der Map-Konstante analog 248 Key-Value-Paare mit englischen Texten.
3. **`de.ts`**: 248 deutsche Texte (primär — Fragen 1:1 aus der Quelle,
   Antworten neu formuliert).
4. **`es.ts`, `fr.ts`, `it.ts`**: Parallel-Übersetzungen — strikt gleiche
   Keys, sonst schlägt `tsc --strict` fehl.
5. Keine Änderungen an `SupportChat.tsx`, `faq.ts`-`buildFuse`/`searchFaq`
   (funktionieren generisch über alle Einträge).

## Verifikation
1. `cd web && npm run type-check` — muss ohne Fehler durchlaufen
   (Union-Type `DictionaryKey` erzwingt, dass alle 5 Dictionaries vollständig
   sind; dies ist die härteste Prüfung).
2. `cd web && npm run lint`.
3. `cd web && npm run dev`, Support-Chat öffnen:
   - Es werden weiterhin die **5 bestehenden** Vorschläge gezeigt
     (`valueBet`, `accuracy`, `dataSource`, `snapshotUpdate`, `kelly`).
   - Stichproben-Suchen (DE): „was ist 1x2", „btts", „kelly kriterium",
     „asian handicap", „chasing losses", „overfitting", „closing line value",
     „cash out" → liefern jeweils passende Antwort statt `support.fallback`.
   - Sprachwechsel (EN/ES/FR/IT) → Antworten in Zielsprache.
4. Git-Diff-Check: **Keine** Änderung an `SupportChat.tsx` oder am
   `slice(0, SUGGESTION_LIMIT)`.

## Risiken / Edge Cases
- **Bundle-Größe**: +~30 KB `faq.ts`, +~40 KB pro Dictionary. Akzeptabel
  (Dictionaries sind bereits ~16–20 KB).
- **Fuse-Threshold (0.45)** evtl. zu strikt bei 124 Einträgen → bei
  Verifikation prüfen; bleibt zunächst unverändert, da der Nutzer
  „nur interne Logik erweitern" möchte und keine UX-Änderung wünscht.
- **Strict TS `Dictionary`-Shape** ist `Record<DictionaryKey, string>` und
  erzwingt automatisch, dass alle 5 Locales alle neuen Keys definieren.
