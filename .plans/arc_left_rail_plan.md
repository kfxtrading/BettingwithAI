# Plan – Arc-inspired Left Rail für die Landing Page

## 1. Ausgangslage

- Landing Page (`web/app/[locale]/page.tsx` → `web/app/HomeClient.tsx`) rendert heute **einspaltig** innerhalb von `main.mx-auto.max-w-page` (1120 px) in `web/app/layout.tsx:134`.
- Oben eine horizontale `Nav` (`web/components/Nav.tsx`) mit Links *Today / Performance / Leagues* + `LanguageSwitcher`.
- Inhalt der Landing: Headline → Value-Bet-Grid → Predictions-Grid → `PerformanceTracker` → `RecentBets`.
- Die „freie linke Seite" meint nicht einen existierenden, leeren Raum, sondern **das Whitespace links/rechts des zentrierten 1120-px-Blocks** auf großen Viewports. Ein Arc-artiges, festes **Left Rail** (Sidebar) soll dort leben und die Top-Nav auf Desktop ablösen.
- Design-System ist bereits sehr „Arc-like": warme Sand-Palette mit Terracotta-Accent (`--bg 250 248 245`, `--accent 212 101 74`), `surface-card`, 14 px Radius, `focus-ring`, `press`. Das lässt sich 1:1 weiternutzen.

## 2. Ziel

Ein **Arc-inspiriertes, vertikales Left Rail** bauen, das die namensgebenden Arc-Features sinnvoll auf die Domäne „AI-Football-Betting" überträgt – KEIN Browser-Klon, sondern „Arc für Value-Bets".

## 3. Mapping: Arc-Feature → Landing-Page-Feature

| Arc | Hier sinnvoll als | Komponente |
|---|---|---|
| **Vertical Sidebar / Pinned Tabs** | Sticky **Left Rail** mit Icons für Ligen (BL / PL / SA / LL / ELC) als „pinned" – aktiver Space = aktueller Ligen-Filter. | `LeftRail` |
| **Favoriten oben** | Kleine Quick-Links: *Today*, *Value Bets*, *Predictions*, *Performance*, *Track Record*, *Methodology* – je mit Icon, springen per Anchor zur Section der Landing Page bzw. zu Unterseiten. | `RailQuickLinks` |
| **Today Tabs (Auto-Archiv)** | Block **„Today"** mit Live-Countdown bis zur nächsten Snapshot-Regenerierung + Kickoff-Ticker der nächsten 3 Matches (nutzt bereits vorhandene `predictions[*].is_live` / `kickoff`). Verfällt visuell nach Anpfiff. | `RailTodayFeed` |
| **Spaces & Profile (Farbe/Icon pro Kontext)** | **League Spaces**: jede Liga hat eigenes Icon + Akzent-Farbton. Auswahl im Rail schaltet `league` in `HomeClient` (ersetzt `LeagueSwitcher` als primäres UI; Switcher bleibt als Fallback). | `RailSpaces` |
| **Arc Max / 5-Second Previews** | **„Match Preview" on Hover**: Hover über einen Value-Bet/Prediction-Card-Titel im Hauptbereich triggert ein schwebendes Mini-Panel im Rail mit Kurz-Erklärung (Edge, Top-Feature-Treiber, Form-Chips). Nutzt existierende `prediction` / `value_bet` Felder – rein deterministische „Story", keine Live-LLM-Calls. | `RailPreviewPanel` |
| **Ask on Page (Cmd + F)** | **„Ask the Model"-Command-Palette** am unteren Rail-Rand (`⌘K`), die per Fuzzy-Search Teams, Ligen, Matches, Methodology-Artikel findet. Server-seitige Daten existieren bereits über `api.leagues` und `content/learn`. | `RailCommandPalette` |
| **Split View** | **Compare-Mode-Toggle**: Rail-Button „Compare" legt Predictions-Grid im Hauptbereich in 2-spaltiges Side-by-Side-Layout um (z. B. Modell-Probabilitäten vs. Markt-Implied). Nur Layout-Switch, keine neue Datenquelle. | Zustand in `LandingContext` |
| **Boosts** | **„View"-Presets** im Rail: *Calm* (nur Value Bets), *Pro* (alle Sections + KPIs), *Mini* (kompakte Dichte). Schaltet CSS-Klassen an `<main>`. | `RailViewPresets` |
| **Air Traffic Control** | **Pinned Matches**: User kann im Rail bis zu 3 Matches „pinnen", die persistent in `localStorage` landen und oben im Today-Feed bleiben. | Teil von `RailTodayFeed` |
| **Little Arc** | **Floating Match Popover**: Klick auf ein Rail-Pinned-Match öffnet ein leichtes, schwebendes Detail-Fenster (Portal), ohne Route-Change. | `FloatingMatchPopover` |

## 4. Layout-Änderungen

### 4.1 Grid
- `web/app/layout.tsx`: `<main>` von `mx-auto max-w-page` auf ein **2-Spalten-Grid** umstellen:
  ```
  grid-cols-[260px_minmax(0,1fr)]  xl:grid-cols-[280px_minmax(0,1120px)]  gap-8
  ```
  Auf `< lg` kollabiert das Rail zu einer **Bottom-Drawer-Nav** (bestehende `Nav` bleibt dort als Mobile-Fallback sichtbar).
- Top-`Nav` auf Desktop (`lg:`): Links werden per `lg:hidden` ausgeblendet, `LanguageSwitcher` wandert in den Rail-Footer.

### 4.2 Neue Komponente `components/rail/LeftRail.tsx`
Struktur (top → bottom):
1. Logo-Badge (analog `Nav.tsx:26-30`).
2. `RailQuickLinks` (Today / Value Bets / Predictions / Performance / Leagues / Learn).
3. `RailSpaces` (League-Icons mit aktivem Accent; setzt `league` via Context).
4. `RailTodayFeed` (nächste 3 Kickoffs + Pinned Matches + Snapshot-Countdown, nutzt `todayQuery.data.generated_at`).
5. `RailViewPresets` (Chip-Toggle: Calm / Pro / Mini).
6. `RailCommandPalette`-Trigger + `LanguageSwitcher` + Theme-Indikator.

### 4.3 Zustands-Hoisting
- `league` + `viewPreset` + `pinnedMatches` + `compareMode` wandern aus `HomeClient` in einen neuen `LandingContext` (`app/LandingContext.tsx`). `HomeClient` und `LeftRail` konsumieren den Context statt eigenem `useState`.

## 5. Komponenten-Inventar (neu)

- `web/components/rail/LeftRail.tsx`
- `web/components/rail/RailQuickLinks.tsx`
- `web/components/rail/RailSpaces.tsx`
- `web/components/rail/RailTodayFeed.tsx`
- `web/components/rail/RailViewPresets.tsx`
- `web/components/rail/RailCommandPalette.tsx` (leichtes Custom-Dialog-Pattern, keine neue Dep)
- `web/components/rail/RailPreviewPanel.tsx` (Phase 2)
- `web/components/rail/FloatingMatchPopover.tsx` (Phase 2)
- `web/app/LandingContext.tsx`

Wiederverwendet: `FormChip`, `ProbabilityBar`, `InfoTooltip`, `.pill`-Utilities.

## 6. i18n

Neue Keys in allen 5 Locales (`web/lib/i18n/*.ts`) – Übersetzungen als ToDo im selben PR:
- `rail.section.quicklinks`, `rail.section.spaces`, `rail.section.today`, `rail.section.views`
- `rail.views.calm|pro|mini`
- `rail.today.nextKickoff`, `rail.today.snapshotRefresh`, `rail.today.pin`, `rail.today.unpin`
- `rail.cmd.placeholder`, `rail.cmd.hint`
- `rail.a11y.toggle`

## 7. Styling-Hinweise (konsistent zum System)

- Rail: `surface-card`-Look mit `border-r` statt Rundung rechts, `bg-surface/70 backdrop-blur`, sticky (`sticky top-0 h-screen`).
- Icons: inline-SVG analog `app/icon.svg` – keine neue Icon-Lib einziehen, falls `package.json` keine enthält.
- Space-Icons animieren Akzent-Farbe pro Liga über CSS-Variable `--accent` lokal per `style={{'--accent': …}}`.
- Hover-Previews: 180 ms `transitionTimingFunction: ease` (bereits definiert).

## 8. Umsetzung in Phasen

**Phase 1 (MVP, 1 PR)**
- Layout-Grid + `LeftRail` + `RailQuickLinks` + `RailSpaces` (ersetzt `LeagueSwitcher` als Primär-UI) + `RailTodayFeed` (Kickoffs + Countdown, ohne Pin).
- `LandingContext` + `HomeClient`-Refactor.
- Mobile-Fallback: Rail auf `< lg` versteckt, Top-`Nav` bleibt.

**Phase 2 (Nice-to-have)**
- `RailViewPresets` (Calm/Pro/Mini).
- Pinned Matches (`localStorage`) + `FloatingMatchPopover`.
- `RailCommandPalette` (⌘K).
- `RailPreviewPanel` (Hover-Previews über Match-Cards).

**Phase 3 (optional)**
- „Ask on Page" echt mit Backend-Endpoint in `src/football_betting/api/` (separater Plan, nicht Teil dieses PRs).

## 9. Dateien

Geändert:
- [./web/app/layout.tsx](./web/app/layout.tsx) – Grid-Wrapper, Nav auf Mobile beschränken.
- [./web/app/HomeClient.tsx](./web/app/HomeClient.tsx) – State via `LandingContext`, optional 2-Spalten-Layout im Compare-Mode.
- [./web/components/Nav.tsx](./web/components/Nav.tsx) – `lg:hidden` + Vereinfachung.
- [./web/lib/i18n/en.ts](./web/lib/i18n/en.ts) und Schwester-Files (`de`, `fr`, `it`, `es`) – neue Keys.
- [./web/tailwind.config.ts](./web/tailwind.config.ts) – optional `gridTemplateColumns.rail`-Token.

Neu:
- [./web/app/LandingContext.tsx](./web/app/LandingContext.tsx)
- [./web/components/rail/LeftRail.tsx](./web/components/rail/LeftRail.tsx) (+ Unterkomponenten aus §5)

## 10. Verifikation

1. `cd web && npm run dev` → Landing auf Desktop (≥ 1280 px) zeigt Rail links, Hauptbereich ≤ 1120 px rechts; Mobile (< 1024 px) unverändert.
2. Klick auf eine Liga im Rail filtert Value-Bets/Predictions identisch zum heutigen `LeagueSwitcher`.
3. Countdown im Rail tickt im 60-s-Intervall synchron zu `todayQuery.refetchInterval`.
4. `npm run lint && npm run type-check` grün.
5. `npm run build` ohne Layout-Shift/Hydration-Warnings.
6. Visuelle Snapshots: Light + Dark (Tailwind `darkMode: 'media'`), EN + DE Locale.
7. Keyboard-Only: Tab-Reihenfolge Rail → Main; `focus-ring` sichtbar.
8. `pytest` + `ruff check . && mypy src` Backend unverändert (keine Python-Änderungen).

## 11. Entscheidungen (vom User bestätigt)

1. **Top-Nav**: bleibt auf Desktop als **schmale Breadcrumb-Leiste** (z. B. `Home / Bundesliga / …`) + `LanguageSwitcher` rechts. Quick-Links wandern komplett ins Rail.
2. **⌘K-Palette**: **Phase 2**. MVP läuft ohne Palette; Phase 2 dann als leichtes `<dialog>` mit Input + Filter über `leagues` und `content/learn`-Slugs, keine neue Dep.
3. **View-Presets**: **Value-only / Full / Compact**.
   - *Value-only* → nur Value-Bets-Section, Rest `hidden`.
   - *Full* → Default.
   - *Compact* → reduziertes `gap`, kleineres Card-Padding, eine Stufe kleinere Schrift — umgesetzt via `data-preset`-Attribut am `<main>` + Tailwind-Selektoren.
4. **Match-Preview**: zweistufig.
   - **Phase 2 (Option A, deterministisch)**: Template aus vorhandenen Snapshot-Feldern (`edge`, `odds`, `kelly_stake`, `form`, Pi-Ratings, Top-Features nach Betrag). Keine externen Calls, 0 € Kosten, kein Latenz-/Moderation-/Key-Handling-Problem.
   - **Phase 3 (Option B, LLM, optional)**: neuer Endpoint `POST /v1/explain/{match_id}` in `src/football_betting/api/routes.py`, ruft Azure OpenAI, Response-Cache pro `match_id + snapshot_generated_at`, Feature-Flag. Erst bauen, wenn A das UX-Muster validiert hat.
