# SEO Backend Extension Plan — Betting with AI

## Goal
Extend the backend so the public site gets indexed by Google. Base language: **English**. Prepare for future **multilingual** support (i18n-ready).

## Context
The "backend that serves HTML" is the **Next.js 14 App Router** in [./web/](./web/). The FastAPI service in [./src/football_betting/api/](./src/football_betting/api/) only emits JSON and is hidden behind CORS — it is not crawled directly. SEO work therefore focuses on Next.js plus a small FastAPI helper endpoint that supplies crawlable data (leagues, teams) used to build the dynamic sitemap.

### Current state (findings)
- [./web/app/layout.tsx](./web/app/layout.tsx): only `title`/`description`, `metadataBase=http://localhost:3000`; `<html lang="en">` hard-coded.
- [./web/app/page.tsx](./web/app/page.tsx), [./web/app/leagues/page.tsx](./web/app/leagues/page.tsx), [./web/app/leagues/%5Bleague%5D/page.tsx](./web/app/leagues/[league]/page.tsx), [./web/app/performance/page.tsx](./web/app/performance/page.tsx): all start with `'use client'` → crawlers receive an empty body; no SSR metadata.
- No `robots.txt`, no `sitemap.xml`, no JSON-LD, no canonical/OG/Twitter tags.
- [./web/next.config.mjs](./web/next.config.mjs): minimal; no i18n config.
- FastAPI already exposes `/leagues`, `/leagues/summaries`, `/leagues/{key}/ratings` ([./src/football_betting/api/routes.py](./src/football_betting/api/routes.py)) — enough data for a dynamic sitemap.
- League keys: `PL, CH, BL, SA, LL` ([./src/football_betting/config.py:50](./src/football_betting/config.py:50)).

## Scope
1. Next.js metadata & indexability (primary).
2. Dynamic `sitemap.xml` + `robots.txt` backed by FastAPI data.
3. Structured data (JSON-LD) on key pages.
4. i18n-ready routing with English as default, scaffolding for `de`.
5. Small FastAPI additions to expose SEO-relevant crawlable slugs.

Out of scope: editorial/blog content, paid SEO tools, AMP.

---

## Implementation Plan

### 1. Environment & config
- Add `NEXT_PUBLIC_SITE_URL` (e.g. `https://bettingwith.ai`) to:
  - [./web/.env.local.example](./web/.env.local.example)
  - [./web/next.config.mjs](./web/next.config.mjs) (expose via `env`).
- Add optional `SITE_URL` to FastAPI env (used by `/seo/*`).

### 2. Global metadata in `layout.tsx`
Edit [./web/app/layout.tsx](./web/app/layout.tsx):
- `metadataBase = new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000')`.
- Rich `Metadata`:
  - `title.default` + `title.template` (`%s · Betting with AI`).
  - Keyword-aware `description` (English).
  - `keywords`, `authors`, `applicationName`, `category: 'sports'`.
  - `openGraph` (type `website`, locale `en_US`, `url`, `images: ['/og.png']`).
  - `twitter` (`summary_large_image`).
  - `alternates.canonical` + `alternates.languages` hreflang stub (`en`, `x-default`, `de`).
  - `robots: { index: true, follow: true, googleBot: { 'max-image-preview': 'large' } }`.
  - `icons`, `manifest`.
- Split the Next 14 `viewport` export out of `metadata`.
- Inject global **Organization + WebSite** JSON-LD via a `<JsonLd>` helper.
- Add `<link rel="preconnect">` to API origin.

### 3. Per-page metadata via server wrappers
Current pages are `'use client'` → split each into:
- `page.tsx` (server component) exporting `generateMetadata()` + rendering a new `*Client.tsx`.
- `*Client.tsx` = current file minus the `'use client'` file (renamed).

Routes:
- [./web/app/page.tsx](./web/app/page.tsx) → Home → JSON-LD `WebSite` + `SportsOrganization`.
- [./web/app/leagues/page.tsx](./web/app/leagues/page.tsx) → `ItemList` JSON-LD.
- [./web/app/leagues/%5Bleague%5D/page.tsx](./web/app/leagues/[league]/page.tsx) → `generateStaticParams` from LEAGUES, dynamic per-league `generateMetadata`, `SportsLeague` JSON-LD.
- [./web/app/performance/page.tsx](./web/app/performance/page.tsx) → static metadata.

### 4. Sitemap & robots (App Router conventions, no new deps)
- **`./web/app/robots.ts`** — exports `MetadataRoute.Robots`: `Allow: /`, `Disallow: /api/`, `sitemap: ${SITE_URL}/sitemap.xml`, `host: SITE_URL`.
- **`./web/app/sitemap.ts`** — exports async `MetadataRoute.Sitemap`:
  - Static: `/`, `/leagues`, `/performance`.
  - Dynamic: one entry per league via `fetch('${API}/leagues', { next: { revalidate: 3600 } })`.
  - Optional v2: per-team entries from `/leagues/{key}/ratings`.
  - `lastModified: new Date()`, `changeFrequency: 'daily'`, `priority` per route.

### 5. FastAPI helper additions
- `GET /seo/slugs` → `{ leagues: [{key, slug, name}], teams: [{league, slug, name}] }` with `Cache-Control: public, max-age=3600`.
  - Implemented in [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py) + [./src/football_betting/api/services.py](./src/football_betting/api/services.py); schema `SeoSlugsOut` in [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py).
- Non-breaking; sitemap can alternatively reuse `/leagues`.

### 6. i18n-ready structure (English default, no heavy lib)
- Add `./web/lib/i18n/locales.ts` — `locales = ['en', 'de'] as const`, `defaultLocale = 'en'`.
- Keep current routes at `/` for English (un-prefixed).
- `./web/middleware.ts` — detect `Accept-Language`, set `NEXT_LOCALE` cookie; **no redirects yet** (avoid breaking prod).
- Populate `alternates.languages` everywhere (both `/en` and `/de` point to `/` in phase 1).
- Add dictionary scaffold `./web/lib/i18n/{en,de}.ts` + a `t(key)` helper — no rendering changes yet, just the infra.

### 7. Crawlable SSR fallback content
Give Google real HTML above the fold:
- Render headings, intros, and league lists on the server inside each `page.tsx` (fetching the new FastAPI helpers).
- Keep interactive UI (React Query, switchers, charts) inside `*Client.tsx` loaded below.

### 8. Core Web Vitals / housekeeping
- `viewport` export in `layout.tsx`.
- `preconnect` to API origin.
- Ensure no hardcoded `localhost` URLs leak into generated HTML.

---

## Files to create / edit

**New**
- [./web/app/robots.ts](./web/app/robots.ts)
- [./web/app/sitemap.ts](./web/app/sitemap.ts)
- `./web/app/HomeClient.tsx`, `./web/app/leagues/LeaguesClient.tsx`, `./web/app/leagues/[league]/LeagueClient.tsx`, `./web/app/performance/PerformanceClient.tsx`
- `./web/components/JsonLd.tsx`
- `./web/lib/seo.ts` (shared `buildMetadata`, canonical, hreflang helpers)
- `./web/lib/i18n/{index,locales,en,de}.ts`
- `./web/middleware.ts`
- `./web/public/og.png` (placeholder, later)

**Edited**
- [./web/app/layout.tsx](./web/app/layout.tsx) — global metadata, viewport, JSON-LD, preconnect.
- [./web/app/page.tsx](./web/app/page.tsx), [./web/app/leagues/page.tsx](./web/app/leagues/page.tsx), [./web/app/leagues/%5Bleague%5D/page.tsx](./web/app/leagues/[league]/page.tsx), [./web/app/performance/page.tsx](./web/app/performance/page.tsx) — become server components with `generateMetadata`.
- [./web/next.config.mjs](./web/next.config.mjs) — expose `NEXT_PUBLIC_SITE_URL`.
- [./web/.env.local.example](./web/.env.local.example) — document new var.
- [./src/football_betting/api/routes.py](./src/football_betting/api/routes.py), [./src/football_betting/api/services.py](./src/football_betting/api/services.py), [./src/football_betting/api/schemas.py](./src/football_betting/api/schemas.py) — add `/seo/slugs`.
- [./tests/test_api.py](./tests/test_api.py) — assert `/seo/slugs` returns expected leagues.

---

## Verification

**Python**
```bash
pytest tests/test_api.py -v
ruff check src/football_betting/api
mypy src/football_betting/api
```

**Next.js** (from `./web`):
```bash
npm run build
npm run lint
npm run type-check
```

**Manual crawl checks** (`fb serve` + `npm run dev`):
- `curl http://localhost:3000/robots.txt` → lists `Sitemap:` line.
- `curl http://localhost:3000/sitemap.xml` → contains `/`, `/leagues`, `/leagues/PL`, `/leagues/BL`, `/performance`.
- `curl -s http://localhost:3000/ | findstr /C:"og:title" /C:"canonical" /C:"application/ld+json"` → tags present.
- `/leagues/PL` view-source → league-specific `<title>` and `<meta description>`.
- Google Rich Results Test on rendered HTML → JSON-LD valid.
- Lighthouse SEO score ≥ 95 on `/` and `/leagues/PL`.

**Production**
- Set `NEXT_PUBLIC_SITE_URL` in Railway (web) and `SITE_URL` in FastAPI.
- Submit `https://<domain>/sitemap.xml` in Google Search Console.
