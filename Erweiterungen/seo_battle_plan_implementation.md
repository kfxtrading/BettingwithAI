# SEO Battle Plan — Implementation Plan

Source strategy: [./Erweiterungen/SEO%20Battle%20Plan.md](./Erweiterungen/SEO%20Battle%20Plan.md)
Builds on: [./Erweiterungen/seo_plan.md](./Erweiterungen/seo_plan.md) (largely shipped)

## What is already in place (no rework needed)

- `metadataBase`, rich `Metadata`, OG/Twitter tags, robots, canonical, hreflang stub: [./web/app/layout.tsx](./web/app/layout.tsx), [./web/lib/seo.ts](./web/lib/seo.ts)
- `sitemap.ts`, `robots.ts`, JSON-LD `Organization`/`WebSite`/`BreadcrumbList`/`SportsOrganization`/`ItemList`
- 5-language i18n scaffold (`en/de/fr/it/es`) and cookie-based locale middleware
- Server pages with `generateMetadata`, client split done for Home/Leagues/League/Performance
- FastAPI `/leagues`, `/leagues/summaries`, `/leagues/{key}/ratings` available

## What is missing vs. the Battle Plan (in scope of this implementation)

The Battle Plan adds three classes of work. We implement everything that is **code-level**; pure content/marketing items (Reddit, AI directories, podcasts, PR pitches) are out of scope here.

---

## Phase A — Indexation & Crawl Hygiene (Week 1, critical)

### A1. Localized URL subdirectories `/en, /de, /fr, /it, /es`
Battle Plan §4 calls this non-negotiable for international indexation; today every locale resolves to `/`, which breaks hreflang in practice (canonical and hreflang point to the same URL for every language, so Google treats them as duplicates).

**Approach (App Router, no extra deps):**
- Add `app/[locale]/` segment containing today's `page.tsx`, `leagues/`, `performance/`, plus the new pages from Phase B.
- Strict gating in `generateStaticParams()` against `locales` from [./web/lib/i18n/locales.ts](./web/lib/i18n/locales.ts).
- `app/page.tsx` + middleware: 308-redirect `/` → `/{detectedLocale}` based on `Accept-Language` cookie (preserves existing UX). Keep `x-default` → `/en/`.
- Update `lib/seo.ts::buildLanguageAlternates(path)` to emit `<link rel="alternate" hreflang="xx" href="/xx{path}">` per locale (currently emits the same URL for every tag — bug).
- Self-referential canonical per locale.
- Update `sitemap.ts` to emit one entry per `(locale, path)` pair (5× current size).
- Update `Nav.tsx`, `LanguageSwitcher.tsx`, all internal `<Link href="...">` to be locale-aware via a `useLocalizedHref()` helper.
- `getServerLocale()` reads the locale from the route params (preferred) instead of the cookie when inside a localized route.

**Files:** new `app/[locale]/layout.tsx`, move pages under `app/[locale]/...`; edit [./web/middleware.ts](./web/middleware.ts), [./web/lib/seo.ts](./web/lib/seo.ts), [./web/lib/i18n/server.ts](./web/lib/i18n/server.ts), [./web/components/Nav.tsx](./web/components/Nav.tsx), [./web/components/LanguageSwitcher.tsx](./web/components/LanguageSwitcher.tsx), [./web/app/sitemap.ts](./web/app/sitemap.ts).

### A2. Split sitemaps
Battle Plan §4: separate `pages`, `matches-upcoming`, `matches-archive`, `blog`. Use the App Router `sitemap.xml` index pattern (`app/sitemap.ts` returning an index that points to multiple route handlers).

**Files:** convert [./web/app/sitemap.ts](./web/app/sitemap.ts) into a sitemap-index, add `app/sitemaps/pages.xml/route.ts`, `app/sitemaps/leagues.xml/route.ts`, placeholder `app/sitemaps/matches-upcoming.xml/route.ts` (pulls from FastAPI `/today`), `app/sitemaps/matches-archive.xml/route.ts` (pulls from a new `/seo/matches/archive` endpoint).

### A3. `/llms.txt`
Battle Plan §7: 30-min asymmetric optionality. Static file under `app/llms.txt/route.ts` listing URLs of methodology, track-record, educational pillars per locale.

### A4. IndexNow
Battle Plan §8 Tier 1. Generate a 32-char key, host `app/{key}.txt/route.ts` returning the key, add a tiny FastAPI helper that POSTs new/changed URLs to `https://api.indexnow.org/indexnow` after `fb snapshot` runs.

**Files:** new `src/football_betting/seo/indexnow.py`, hook into `cli.py::snapshot`, env var `INDEXNOW_KEY`.

### A5. Schema correctness pass
- Add `BreadcrumbList` to layout JSON-LD as a default (currently per-page only; redundancy is fine and Google recommends it).
- Add `WebSite` `potentialAction` `SearchAction` to enable sitelinks search box (Battle Plan §4).
- Self-referential canonicals confirmed on every page.

---

## Phase B — E-E-A-T Pages (Weeks 2–4)

Battle Plan §5 lists these as launch-day priorities. Build under `app/[locale]/`:

| Route | Content | Schema |
|---|---|---|
| `/about` | Founder story, stack, why non-affiliate | `AboutPage`, `Person` |
| `/methodology` | Pi-Ratings, CatBoost, Poisson, MLP ensemble, calibration, retraining cadence, limitations | `Article`, `FAQPage` |
| `/track-record` | Wraps existing `/performance` data — adds calibration plot, ROI vs CLV, **CSV download** | `Dataset` |
| `/model-changelog` | Pulled from [./CHANGELOG.md](./CHANGELOG.md) at build time | `Article` with `dateModified` |
| `/responsible-gambling` | Locale-specific helpline links (BZgA/Check-dein-Spiel DE, Giocaresponsabile IT, Joueurs-info-service FR, Juego Responsable ES, GambleAware EN) | `WebPage` |
| `/impressum` (DE-only) | Legal Impressum required by §5 TMG | `WebPage` |
| `/legal/terms`, `/legal/privacy`, `/legal/cookies` | Copy already partially exists in cookie banner | `WebPage` |

**FastAPI additions:**
- `GET /seo/track-record.csv` — historical predictions vs results (Battle Plan §5 "downloadable CSV is your linkable asset").
- `GET /seo/track-record/calibration` — bins of predicted vs actual probability per league.

**Footer rebuild** [./web/components/Footer.tsx](./web/components/Footer.tsx):
- 4-column grid: Site / Methodology / Legal / Responsible Gambling
- 18+ badge, locale-specific helpline link, "Informational only" disclaimer
- Footer links count as sitewide internal linking signal — currently zero internal links from footer.

---

## Phase C — Content Pillars & Schema (Weeks 5–8)

Battle Plan §6 Pillar A. Implement as MDX so a solo dev can ship content quickly.

### C1. Educational pillar hub
- New route `app/[locale]/learn/` (hub) and `app/[locale]/learn/[slug]/page.tsx`.
- MDX support via `@next/mdx` (single dependency add).
- Content lives in `web/content/learn/{locale}/{slug}.mdx`.
- Slugs (EN first, then DE/IT/ES/FR translation queue):
  `value-bets`, `implied-probability`, `kelly-criterion`, `bankroll-management`, `closing-line-value`, `expected-goals-xg`, `btts-explained`, `over-under-2-5`, `1x2-explained`, `model-accuracy-brier-calibration`.
- Each MDX page uses an `<EducationalArticle>` server wrapper that emits `Article` + `FAQPage` JSON-LD from frontmatter.
- AI-Overview formatting (Battle Plan §7 12-point checklist) baked into the MDX template: TL;DR in first 60 words, H2 questions, bullet lists, definitional callouts.

### C2. League hub upgrade
[./web/app/[locale]/leagues/[league]/page.tsx](./web/app/leagues/[league]/page.tsx):
- Add SSR-rendered "Next 5 fixtures" + "Last 5 results with model accuracy ✓/✗" — Battle Plan §4 archive-with-accuracy strategy.
- Add `SportsOrganization` (already present), upgrade to also emit per-team `SportsTeam` items inside `subOrganization`.
- Localize titles per Battle Plan §2 keyword table (e.g. `Premier League Pronostici, Quote e Analisi IA` for IT).

### C3. Match prediction pages (high-leverage but heavier)
- New route `app/[locale]/leagues/[league]/[match]/page.tsx`.
- 150–300-word AI-generated wrapper per match (gate indexation: `noindex` if wrapper missing, per Battle Plan §4).
- Schema: `AnalysisNewsArticle` + embedded `SportsEvent` with `additionalProperty` probabilities exactly as in Battle Plan §4 sample.
- After kickoff: keep page indexed under `/archive/`, append actual result + correctness flag.

**FastAPI additions:**
- `GET /seo/matches/upcoming?locale=xx` — slugs for sitemap.
- `GET /seo/matches/{slug}` — wrapper prose (use the existing prediction services + a small templated text generator initially).

### C4. Localized metadata strings
[./web/lib/i18n/{de,fr,it,es}.ts](./web/lib/i18n/de.ts) need additional keys:
- `learn.heading`, `learn.description`, per-pillar titles
- Battle Plan §2 keywords per language (`fußball tipps heute`, `pronostici calcio oggi`, `pronostic foot du jour`, `pronósticos fútbol hoy`)
- Per-league localized titles
Add to `DictionaryKey` union in `en.ts` then mirror in all others.

---

## Phase D — Compliance & Trust Signals (parallel to B)

- Strip any "guaranteed/sure win" language from dictionaries (audit all 5 locales) — Battle Plan §10.
- Add `<dl class="meta">` on every editorial page rendering visible "Last updated" date matching `dateModified` schema (Battle Plan §7 #9).
- Confirm cookie banner does not cover >30% viewport on mobile (Battle Plan §4 mobile-first).
- Add `noindex` on user-filter URLs (e.g. `?league=PL`) via a generic `parametrizedNoindex()` middleware check.

---

## Out of scope (per Battle Plan but content/marketing-only)

- AlternativeTo / Tipstrr / Reddit / Trustpilot submissions (manual)
- Press releases via EIN Presswire
- YouTube Shorts / TikTok / Twitter cadence
- Native-editor translation of pillar content
- Backlink outreach via Qwoted/Featured

---

## Files matrix

**New (web)**
- `app/[locale]/layout.tsx`, `app/[locale]/page.tsx`, `app/[locale]/leagues/...`, `app/[locale]/performance/page.tsx`
- `app/[locale]/about/page.tsx`, `app/[locale]/methodology/page.tsx`, `app/[locale]/track-record/page.tsx`, `app/[locale]/model-changelog/page.tsx`, `app/[locale]/responsible-gambling/page.tsx`
- `app/[locale]/legal/{terms,privacy,cookies}/page.tsx`
- `app/de/impressum/page.tsx`
- `app/[locale]/learn/page.tsx`, `app/[locale]/learn/[slug]/page.tsx`
- `app/sitemaps/{pages,leagues,matches-upcoming,matches-archive}.xml/route.ts`
- `app/llms.txt/route.ts`, `app/{INDEXNOW_KEY}.txt/route.ts`
- `components/Footer.tsx` (rewrite), `components/EducationalArticle.tsx`, `components/CalibrationPlot.tsx`, `components/AgeBadge.tsx`
- `lib/localizedHref.ts`
- `content/learn/{en,de,fr,it,es}/*.mdx`

**Edited (web)**
- [./web/app/layout.tsx](./web/app/layout.tsx) — add `WebSite.potentialAction`
- [./web/app/sitemap.ts](./web/app/sitemap.ts) — convert to sitemap index
- [./web/middleware.ts](./web/middleware.ts) — root → locale redirect
- [./web/lib/seo.ts](./web/lib/seo.ts) — fix `buildLanguageAlternates` to be locale-aware per path
- [./web/lib/i18n/server.ts](./web/lib/i18n/server.ts) — read locale from route params
- [./web/lib/i18n/{en,de,fr,it,es}.ts](./web/lib/i18n/en.ts) — add new dictionary keys
- [./web/components/Nav.tsx](./web/components/Nav.tsx), [./web/components/LanguageSwitcher.tsx](./web/components/LanguageSwitcher.tsx)
- [./web/next.config.mjs](./web/next.config.mjs) — MDX support
- [./web/package.json](./web/package.json) — `@next/mdx`, `@mdx-js/react`

**New (Python)**
- `src/football_betting/seo/__init__.py`
- `src/football_betting/seo/indexnow.py`
- `src/football_betting/seo/track_record.py` (CSV + calibration buckets)
- `src/football_betting/seo/match_slugs.py`

**Edited (Python)**
- [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py) — `/seo/track-record.csv`, `/seo/track-record/calibration`, `/seo/matches/upcoming`, `/seo/matches/{slug}`
- [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py) — corresponding schemas
- [./src/football_betting/cli.py](./src/football_betting/cli.py) — IndexNow ping after `snapshot`
- [./tests/test_api.py](./tests/test_api.py) — assertions for new endpoints

---

## Phased rollout (matches Battle Plan §11 90-day roadmap)

1. **PR 1 — Indexation foundation (Phase A1+A2+A5):** localized routes, fixed hreflang, sitemap index. Highest SEO impact, biggest blast radius — ship behind a feature toggle if needed.
2. **PR 2 — `llms.txt` + IndexNow (A3+A4).**
3. **PR 3 — Footer rewrite + E-E-A-T legal pages (Phase B static parts).**
4. **PR 4 — `/about`, `/methodology`, `/track-record` upgrade with `Dataset` schema + CSV (B dynamic).**
5. **PR 5 — MDX learn pillar (Phase C1) — EN content first, translations follow.**
6. **PR 6 — League hub upgrade with archive + accuracy (C2).**
7. **PR 7 — Match prediction pages with `AnalysisNewsArticle` (C3).** Optional, depends on text-generation quality.

---

## Verification

**Per PR**
```bash
cd web && npm run build && npm run lint && npm run type-check
pytest -v
ruff check src/football_betting && mypy src/football_betting
```

**Crawl smoke tests** (after `fb serve` + `npm run dev`):
- `curl http://localhost:3000/` -> 308 to `/en/`
- `curl http://localhost:3000/sitemap.xml` -> sitemap index referencing 4 child sitemaps
- `curl http://localhost:3000/sitemaps/pages.xml` -> contains `/en/`, `/de/`, `/fr/`, `/it/`, `/es/` x static routes
- `curl -s http://localhost:3000/de/leagues/BL | findstr /C:"canonical" /C:"hreflang"` -> self-canonical to `/de/...`, hreflang covers all 5 locales + `x-default`
- `curl http://localhost:3000/llms.txt` -> 200, lists pillar URLs
- Google Rich Results Test on `/en/learn/value-bets`, `/en/leagues/PL`, `/en/track-record` -> no errors, recognizes `Article`/`FAQPage`/`Dataset`/`SportsOrganization`
- Lighthouse SEO score >= 95 on `/en/` and `/de/leagues/BL`

**Production**
- Set `NEXT_PUBLIC_SITE_URL`, `INDEXNOW_KEY` in Railway
- Re-submit `/sitemap.xml` to Google Search Console + Bing Webmaster Tools after PR 1
- Verify "Discovered – currently not indexed" count drops in Coverage report within 7 days
