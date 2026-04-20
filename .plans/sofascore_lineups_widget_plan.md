# Plan: Sofascore "Lineups & Team of the Week" Widget on Match Detail Page

## Goal
Embed the Sofascore Lineups widget (iframe) directly below the prose section
on `/{locale}/leagues/{LEAGUE}/{match-slug}`, gated behind the marketing
cookie-consent category.

## Core Challenge
The snapshot / match wrapper currently has **no** Sofascore `event_id`. It
must be linked at snapshot-build time using the existing Sofascore scraper
(which already exposes the id, see
[./src/football_betting/scraping/sofascore.py:280](./src/football_betting/scraping/sofascore.py:280))
and pushed through the API to the frontend.

## Files to touch

### Backend (Python)
1. **[./src/football_betting/scraping/sofascore.py](./src/football_betting/scraping/sofascore.py)**
   New helper `match_event_for_fixture(home, away, date_utc) -> int | None`
   (uses existing `get_scheduled_events`, fuzzy team-name match within +/- 1
   day window).
2. **Snapshot builder** (locate via grep for `today.json`, likely
   `predict/predict_today.py` or `features/builder.py`):
   add `sofascore_event_id: int | None` per fixture, only filled when
   `SCRAPING_ENABLED=1`.
3. **[./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py)** lines 288-305
   Extend `MatchWrapperOut` with `sofascore_event_id: int | None = None`.
4. **[./src/football_betting/api/services.py](./src/football_betting/api/services.py)** lines 1055-1092
   `get_match_wrapper`: pass `sofascore_event_id` from snapshot through.
5. **[./src/football_betting/seo/match_slugs.py](./src/football_betting/seo/match_slugs.py)**
   Extend `MatchPrediction`/`MatchWrapper` dataclasses + `find_match_in_snapshot`
   to read the new field from JSON.
6. **Tests**: `tests/test_seo_match_slugs.py`, `tests/test_api_routes.py`
   cover both with and without `sofascore_event_id`.

### Frontend (Next.js / TS)
7. **New `web/components/SofascoreLineupsWidget.tsx`** (client component)
   - Props: `eventId: number`, `homeTeam: string`, `awayTeam: string`.
   - Reads consent via `localStorage` key `bwai.cookie-consent.v1`,
     category `marketing` (mirrors pattern in
     [./web/components/CookieConsent.tsx](./web/components/CookieConsent.tsx)).
   - Without consent: render placeholder card (`surface-card` style) +
     button "Load Sofascore lineups" (per-instance opt-in, does not flip the
     global consent flag).
   - With consent: render iframe
     ```tsx
     <iframe
       src={`https://widget.sofascore.com/?id=${eventId}&widgetTitle=lineups&type=lineups`}
       title={`Sofascore lineups: ${homeTeam} vs ${awayTeam}`}
       loading="lazy"
       sandbox="allow-scripts allow-same-origin allow-popups"
       className="h-[760px] w-full rounded-md border border-white/10"
     />
     ```
   - Verify exact widget URL once via
     `https://widgets.sofascore.com/config/lineups`; copy iframe template
     from there into a single constant in this component.
8. **[./web/app/[locale]/leagues/[league]/[match]/page.tsx](./web/app/%5Blocale%5D/leagues/%5Bleague%5D/%5Bmatch%5D/page.tsx)** line 196-200
   - Extend local `MatchWrapper` type with
     `sofascore_event_id?: number | null`.
   - Insert directly **below** the `<section>` rendering `wrapper.prose`
     (after line 200):
     ```tsx
     {wrapper.sofascore_event_id && (
       <section className="mt-8">
         <h2 className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-muted">
           {dict['match.lineups.title']}
         </h2>
         <SofascoreLineupsWidget
           eventId={wrapper.sofascore_event_id}
           homeTeam={wrapper.home_team}
           awayTeam={wrapper.away_team}
         />
         <p className="mt-2 text-2xs uppercase tracking-[0.08em] text-muted">
           {dict['match.lineups.attribution']}
         </p>
       </section>
     )}
     ```
9. **i18n keys** `match.lineups.title`, `match.lineups.attribution`,
   `match.lineups.consentPrompt` in all 5 locales:
   [./web/lib/i18n/de.ts](./web/lib/i18n/de.ts),
   [./web/lib/i18n/en.ts](./web/lib/i18n/en.ts),
   [./web/lib/i18n/es.ts](./web/lib/i18n/es.ts),
   [./web/lib/i18n/fr.ts](./web/lib/i18n/fr.ts),
   [./web/lib/i18n/it.ts](./web/lib/i18n/it.ts).
10. **Privacy / impressum**: add note that activating the widget transmits
    data to `sofascore.com`
    (`web/app/[locale]/legal/...` and impressum page).

## Non-goals
- No re-implementation of the lineup view; we use the official iframe so
  live updates and player ratings come straight from Sofascore.
- No automatic flip of marketing consent; user opts in either per-match or
  through the global consent banner.
- League standings widget from the previous plan is explicitly out of scope.

## Verification (end-to-end)

1. **Backend**:
   ```bash
   set SCRAPING_ENABLED=1
   fb snapshot
   curl http://localhost:8000/seo/matches/<slug> | jq .sofascore_event_id
   ```
   should return an integer id (e.g. `12345678`).
2. **Frontend**:
   ```bash
   cd web && npm run dev
   ```
   - Open e.g. `/de/leagues/PL/aston-villa-vs-sunderland-...`.
   - Without consent: placeholder visible, **no** request to
     `widget.sofascore.com` in DevTools.
   - Grant marketing consent -> iframe loads; lineup with Sofascore
     ratings visible; `max-w-3xl` layout intact.
3. **Fallback**: match without `sofascore_event_id` -> section is omitted,
   no empty block, no console errors.
4. **Quality gates**:
   ```bash
   ruff check . && mypy src && pytest -q
   cd web && npm run lint && npm run type-check && npm run build
   ```
5. **Lighthouse** (match page, with consent): LCP regression < 200 ms, CLS
   unchanged (iframe has fixed height).

## Risks & mitigation
- **Event-id matching unreliable** (team-name aliasing): reuse the
  team-name normalisation already in `features/builder.py`; on multiple
  matches leave the field empty rather than embed the wrong event.
- **Widget URL may change**: keep URL template in one constant inside
  `SofascoreLineupsWidget.tsx`.
- **GDPR**: strictly behind marketing consent; update privacy text.
