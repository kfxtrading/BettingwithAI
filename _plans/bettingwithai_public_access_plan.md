# Plan: Fix public access, redirects and SSR for bettingwithai.app

## Context / reported symptoms
- `https://www.bettingwithai.app` fails in headless tools; `https://bettingwithai.app/` sometimes times out; `http://bettingwithai.app` works and redirects to `/en`.
- Home shows only `Loading predictions…` in initial HTML.
- `/en/performance` shows placeholder KPIs (`Bets —`, `Hit rate —`, `ROI —`, `Max drawdown —`) and `No settled bets per league yet.` in the first HTML response.
- `/en/leagues` is routable but initial HTML contains no league tiles / ratings, only the heading.
- Static pages (About, Methodology, Terms, Privacy, Cookies, Responsible Gambling) work fine.
- About page claims source code and changelog are public but navigation exposes no link.

## Root causes (from code inspection)

1. **CSR-only critical pages.** The three pages that hold the main product data all import a client component that fetches via React Query with `cache: 'no-store'`:
   - [./web/app/[locale]/page.tsx](./web/app/%5Blocale%5D/page.tsx) → `<HomeClient />` ([./web/app/HomeClient.tsx](./web/app/HomeClient.tsx))
   - [./web/app/[locale]/performance/page.tsx](./web/app/%5Blocale%5D/performance/page.tsx) → `<PerformanceClient />` ([./web/app/performance/PerformanceClient.tsx](./web/app/performance/PerformanceClient.tsx))
   - [./web/app/[locale]/leagues/page.tsx](./web/app/%5Blocale%5D/leagues/page.tsx) fetches `fetchLeaguesServer()` only for JSON-LD but renders the empty `<LeaguesClient />` ([./web/app/leagues/LeaguesClient.tsx](./web/app/leagues/LeaguesClient.tsx)), which re-queries client-side.
   Result: crawlers, previews, and any no-JS reader see only skeletons / placeholders.

2. **Domain / redirect chain not authoritative.** Middleware in [./web/middleware.ts](./web/middleware.ts) only handles locale prefix (`/` → `/<locale>/...` via 308). Nothing normalises `www` vs apex or `http` vs `https`. That is left to Railway's edge; the reported inconsistency (apex timeout, www not reachable, http works) indicates the Railway custom-domain entry has only one of the hostnames attached or the TLS cert is issued for only one name.

3. **Locale redirect is unconditional 308 for any first-party visit to `/`.** Headless clients that don't send `Accept-Language` cleanly get redirected immediately; if the redirect target is the non-attached hostname variant they appear to "time out." Middleware also runs on HEAD requests.

4. **`NEXT_PUBLIC_API_URL` default is `http://localhost:8000`** ([./web/lib/api.ts](./web/lib/api.ts), [./web/next.config.mjs](./web/next.config.mjs)). If the Railway web service is deployed without that env var set, the browser bundle tries to fetch from `localhost:8000` and every data section stays in the loading state indefinitely — consistent exactly with the reported "Loading predictions…".

5. **About page text claims public source code / changelog** ([./web/app/[locale]/about/page.tsx](./web/app/%5Blocale%5D/about/page.tsx)) but [./web/components/Footer.tsx](./web/components/Footer.tsx) and header navigation do not expose these links.

## Fix plan

### 1. Make the three data pages SSR-first with client hydration fallback
For each page: fetch the payload server-side, pass it as `initialData` into the React Query client (via a `HydrationBoundary` or as a prop). Keep `'use client'` children for interactivity (league switcher, refetching).

Files to modify:
- [./web/app/[locale]/page.tsx](./web/app/%5Blocale%5D/page.tsx): `await` snapshot of `/predictions/today` and `/leagues`, pass to `HomeClient`.
- [./web/app/HomeClient.tsx](./web/app/HomeClient.tsx): accept `initialToday`, `initialLeagues` props and use `useQuery({ initialData })`.
- [./web/app/[locale]/performance/page.tsx](./web/app/%5Blocale%5D/performance/page.tsx): `await` `/performance/summary` and `/performance/bankroll`.
- [./web/app/performance/PerformanceClient.tsx](./web/app/performance/PerformanceClient.tsx): accept `initialSummary`, `initialBankroll`.
- [./web/app/[locale]/leagues/page.tsx](./web/app/%5Blocale%5D/leagues/page.tsx): `await fetchLeagueSummariesServer()` and pass to `LeaguesClient`.
- [./web/app/leagues/LeaguesClient.tsx](./web/app/leagues/LeaguesClient.tsx): accept `initialSummaries`.
- [./web/lib/server-api.ts](./web/lib/server-api.ts): add `fetchTodayServer`, `fetchPerformanceSummaryServer`, `fetchBankrollServer`, `fetchLeagueSummariesServer`. Use `next: { revalidate: 60 }` for today and `{ revalidate: 300 }` for performance.

Error / empty handling: if the server fetch fails (API down), render the existing `Empty` state so initial HTML is still meaningful — the client query can still retry.

### 2. Guarantee `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_SITE_URL` at runtime
- Document required Railway env vars in [./web/.env.local.example](./web/.env.local.example) and add a build-time assertion in [./web/next.config.mjs](./web/next.config.mjs) that throws if `NEXT_PUBLIC_API_URL` is missing in `NODE_ENV === 'production'`.
- Add a server-only `API_INTERNAL_URL` fallback (Railway private networking) in `server-api.ts` so SSR can call the API over the internal network even when the public URL is blocked.

### 3. Domain / redirect normalisation
- In [./web/middleware.ts](./web/middleware.ts) add an early redirect:
  1. If `x-forwarded-host` is `www.bettingwithai.app`, 308 → `bettingwithai.app` (pick apex as canonical — matches current `SITE_URL`).
  2. If `x-forwarded-proto === 'http'` (Railway sets it), 308 → `https`.
- Railway config: attach **both** `bettingwithai.app` and `www.bettingwithai.app` as custom domains on the web service so TLS certs exist for both; Railway auto-generates Let's Encrypt for each.
- Keep locale redirect as today, but short-circuit it for `/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/indexnow/*` (already excluded via `matcher`, verify) and for `HEAD` requests (return 200 without redirect so uptime checks don't chain).

### 4. Add a public JSON surface for reader-only tools
The FastAPI `/predictions/today` already returns JSON, but it lives under a different origin / possibly blocked by CORS for third parties. Option: expose read-only proxy routes on the Next.js side at `/api/today`, `/api/performance`, `/api/leagues` (server handlers calling `server-api.ts`) so third-party readers that can reach the frontend domain can get data too.

Files:
- New: `./web/app/api/today/route.ts`, `./web/app/api/performance/route.ts`, `./web/app/api/leagues/route.ts`.

### 5. Minor content fix — About claim vs navigation
- Edit [./web/components/Footer.tsx](./web/components/Footer.tsx) (and/or header nav) to add a "Source code" link (to the repo URL) and a "Changelog" link (to `/legal`-style editorial page or external `CHANGELOG.md`). Alternatively, soften the About copy in [./web/app/[locale]/about/page.tsx](./web/app/%5Blocale%5D/about/page.tsx) to match what is actually linked from the site.

### 6. Healthchecks & uptime probe
- Add a lightweight `/healthz` route in the Next.js app (`./web/app/healthz/route.ts`) that returns `200 "ok"` without running middleware (exclude from the matcher). Point Railway's web-service healthcheck at it to stop the apex-timeout reports caused by redirect chains during probes.

## Files to touch (summary)
- Edit: [./web/middleware.ts](./web/middleware.ts), [./web/next.config.mjs](./web/next.config.mjs), [./web/lib/server-api.ts](./web/lib/server-api.ts), [./web/app/[locale]/page.tsx](./web/app/%5Blocale%5D/page.tsx), [./web/app/HomeClient.tsx](./web/app/HomeClient.tsx), [./web/app/[locale]/performance/page.tsx](./web/app/%5Blocale%5D/performance/page.tsx), [./web/app/performance/PerformanceClient.tsx](./web/app/performance/PerformanceClient.tsx), [./web/app/[locale]/leagues/page.tsx](./web/app/%5Blocale%5D/leagues/page.tsx), [./web/app/leagues/LeaguesClient.tsx](./web/app/leagues/LeaguesClient.tsx), [./web/components/Footer.tsx](./web/components/Footer.tsx), [./web/.env.local.example](./web/.env.local.example).
- Create: `./web/app/api/today/route.ts`, `./web/app/api/performance/route.ts`, `./web/app/api/leagues/route.ts`, `./web/app/healthz/route.ts`.
- Config: Railway custom domains (both apex + www), confirm `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_SITE_URL` env vars on the web service.

## Verification

1. Build and run both services locally:
   ```
   pip install -e ".[api]" && uvicorn football_betting.api.app:create_app --factory --port 8000
   cd web && npm install && NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_SITE_URL=http://localhost:3000 npm run build && npm start
   ```
2. `curl -sS http://localhost:3000/en | rg -i "loading predictions"` should return nothing; `rg -i "Value Bets"` should match; predictions grid markup must appear in the raw HTML.
3. `curl -sS http://localhost:3000/en/performance | rg "Hit rate"` must include real numbers (or the explicit `0` / `—` coming from the server payload, not the pre-hydration placeholder).
4. `curl -sS http://localhost:3000/en/leagues | rg "BL|PL|SA"` should match league tiles.
5. `curl -I http://localhost:3000/healthz` → `200 OK` without redirect.
6. `curl -I -H "Host: www.bettingwithai.app" https://bettingwithai.app/` (after deploy) → 308 to apex; `curl -I http://bettingwithai.app/` → 308 to `https://bettingwithai.app/`.
7. `pytest` (backend) and `cd web && npm run lint && npm run type-check` stay green.
8. After deploy, re-run the reporter's headless checks against `https://bettingwithai.app`, `https://www.bettingwithai.app`, `http://bettingwithai.app` and confirm all three resolve to `https://bettingwithai.app/<locale>` with populated HTML.
