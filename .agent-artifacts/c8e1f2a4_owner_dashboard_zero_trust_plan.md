# Plan — Owner-only Investor Inbox Dashboard behind Cloudflare Access (Zero Trust + Passkey/FIDO2)

## Goal

Replace the existing password-protected `/admin/inquiries` flow with a hardened **owner-only dashboard** that surfaces incoming investor mails (the inquiries already captured via the public `/investors/contact` form). The dashboard must satisfy:

- **Public site** lives on the apex / `www.bettingwithai.app`.
- **Internal dashboard** lives on a separate hostname: `ops.bettingwithai.app` (preferred) or `internal.bettingwithai.app`.
- A **Zero-Trust layer (Cloudflare Access)** sits in front of the entire internal hostname.
- **Authentication = Passkey only**, with **two FIDO2 hardware keys as backup**.
- **No public owner-login UI in the app itself** — the app must not even render a login form on the public origin. An attacker only ever sees the Cloudflare Access challenge (or nothing at all if the host is unknown to them).

## Constraints / Non-goals

- Do not introduce a new backend (Python). Everything stays in `.\web\`.
- Do not add a self-hosted WebAuthn implementation in the app — rely on Cloudflare Access's own Passkey/FIDO2 enforcement at the edge. This avoids credential storage in our app and keeps the auth surface = 0.
- Do not break the public `/investors/contact` form, the API route, or the JSON store.
- Do not expose any owner-only routes on the public hostname.

## Current state (relevant files)

- Public form: `.\web\app\[locale]\investors\contact\page.tsx` → `.\web\components\InvestorInquiryForm.tsx`
- API ingest: `.\web\app\api\investors\route.ts`
- Storage: `.\web\lib\inquiries.ts` (JSON file at `data/investor-inquiries.json` or `INVESTOR_INQUIRY_STORE`)
- Existing admin (to be retired/repurposed):
  - `.\web\app\admin\layout.tsx`
  - `.\web\app\admin\page.tsx`
  - `.\web\app\admin\inquiries\page.tsx`
  - `.\web\app\admin\inquiries\[id]\` (detail/reply)
  - `.\web\app\admin\login\page.tsx`           ← REMOVE (no public login)
  - `.\web\app\api\admin\login\route.ts`        ← REMOVE
  - `.\web\app\api\admin\logout\route.ts`       ← REMOVE (or keep as no-op clear)
  - `.\web\components\AdminLoginForm.tsx`       ← REMOVE
  - `.\web\lib\adminAuth.ts`                    ← REPLACE with Access-JWT verification
- Routing/host handling: `.\web\middleware.ts` (currently force-redirects `www.` → `bettingwithai.app`; **must be host-aware** to allow `ops.*` through untouched and to keep `/admin` off the public host).
- Build env guards: `.\web\next.config.mjs`

## Architecture

```
                                     ┌────────────────────────────────────────┐
Investor ──HTTPS──▶ www.bettingwithai│ Next.js (public)                       │
                                     │  /[locale]/investors/contact ──▶ POST  │
                                     │  /api/investors  ──▶ writes JSON store │
                                     └──────────────┬─────────────────────────┘
                                                    │ shared volume / same app
                                                    ▼
                                     ┌────────────────────────────────────────┐
Owner ──HTTPS──▶ ops.bettingwithai   │ Cloudflare Access (Zero Trust)         │
                                     │  Policy: identity = owner@…            │
                                     │  Auth method = Passkey / FIDO2 only    │
                                     │  Issues signed CF-Access-JWT cookie    │
                                     └──────────────┬─────────────────────────┘
                                                    │ origin request (mTLS or
                                                    │ Cloudflare Tunnel)
                                                    ▼
                                     ┌────────────────────────────────────────┐
                                     │ Next.js (same deployment)              │
                                     │  Host-gate: only ops.* serves /admin   │
                                     │  Verifies Cf-Access-Jwt-Assertion      │
                                     │  /admin/inquiries (read JSON store)    │
                                     └────────────────────────────────────────┘
```

Same Next.js deployment serves both hostnames; the **hostname** is the gate, not the path. Cloudflare Access protects the entire `ops.*` hostname before it touches the origin.

## Cloudflare configuration (out-of-repo, but specified)

1. **DNS**: add `ops.bettingwithai.app` (proxied through Cloudflare, orange cloud) pointing at the same origin (Railway service or Cloudflare Tunnel).
2. **Cloudflare Tunnel (recommended)**: run `cloudflared` on the origin so the origin has no public IP at all; the tunnel only exposes `ops.*` through Access. (Optional but strongly recommended — fulfils "attacker can't even reach the login page".)
3. **Access Application** (Zero Trust dashboard → Access → Applications → Self-hosted):
   - Application domain: `ops.bettingwithai.app` (covers entire host).
   - Session duration: 8 h.
   - **Identity provider = One-time PIN to owner email + WebAuthn**, OR a dedicated IdP (e.g. GitHub) — but the **policy requires `purpose_justification = false` AND auth method = WebAuthn (Passkey)**.
4. **Access Policy**:
   - Action: **Allow**.
   - Include: `email == owner@bettingwithai.app`.
   - Require: **Authentication method = WebAuthn** (this is what enforces Passkey/FIDO2; passwords/OTP-only are rejected).
5. **WebAuthn registration**: enroll **3 authenticators** for the owner identity:
   - 1 platform Passkey (e.g. iCloud Keychain / Windows Hello / Android).
   - 2 roaming **FIDO2 hardware keys** (e.g. YubiKey 5 + 1 backup) — registered as "security keys" in the Access end-user dashboard.
6. **Bot Fight / WAF**: enable "Block known bots" rule for `ops.*`; rate-limit `/admin/*` to 60 req/min.
7. **Service Token (optional)** for any automation that must hit `ops.*` non-interactively — out of scope for the dashboard itself.

These steps are documented in a new short ops note and referenced from `README.md` (only if the user later asks; this plan does not auto-create docs).

## App-side changes (in `.\web\`)

### A. New host-aware middleware

Edit `.\web\middleware.ts`:

- Compute `hostname` early (already done for canonical-host redirect).
- Define `INTERNAL_HOST = process.env.INTERNAL_HOST ?? 'ops.bettingwithai.app'`.
- **Public host (`bettingwithai.app` / `www.*`)**:
  - If pathname starts with `/admin` → return `404` (`NextResponse.rewrite` to `/_not-found`) so the public origin denies even the existence of the dashboard.
  - Existing locale logic unchanged.
- **Internal host (`ops.*`)**:
  - Skip locale redirects entirely.
  - Skip canonical-host redirect (do not rewrite `ops.*` → apex).
  - Allow only `/admin/*`, `/api/admin/*`, `/healthz`, `/_next/*`. Everything else → `404`.
  - Verify the Cloudflare Access JWT (see B). If missing/invalid → `403` with text "Access required" (Access should already have blocked this; defence-in-depth).
- Update `config.matcher` to include `/admin` and `/api/admin/*` paths (currently `admin` is excluded from matcher — we need it included so the host check runs).

### B. New auth lib: Cloudflare Access JWT verification

Replace `.\web\lib\adminAuth.ts` with a verifier that trusts only Cloudflare Access:

- Reads header `Cf-Access-Jwt-Assertion` (or cookie `CF_Authorization`).
- Fetches and caches Cloudflare's signing keys from
  `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/certs`
  (env: `CF_ACCESS_TEAM_DOMAIN`).
- Verifies signature (RS256), `aud` = `CF_ACCESS_AUD` env, `iss` = team domain, `exp` not expired.
- Returns the decoded `email` claim.
- Exports:
  - `getAccessIdentity(): Promise<{ email: string } | null>` for Server Components (uses `headers()`).
  - `requireOwner()` helper that `redirect`s to a static `/admin/forbidden` page (rendered only on `ops.*`) if the email does not match `OWNER_EMAIL`.
- Use `jose` (already small, ESM, no native deps). Add to `.\web\package.json` only if not present — confirm before adding.

### C. Strip the in-app password login

Delete:
- `.\web\app\admin\login\page.tsx`
- `.\web\app\api\admin\login\route.ts`
- `.\web\app\api\admin\logout\route.ts`
- `.\web\components\AdminLoginForm.tsx`

Update:
- `.\web\app\admin\inquiries\page.tsx` — replace `isAdminAuthenticated()` + `redirect('/admin/login…')` with `await requireOwner()`. On failure render a minimal "Access denied" message (no link to log in — there is no app-level login).
- `.\web\app\admin\inquiries\[id]\page.tsx` and any reply route under `.\web\app\api\admin\inquiries\[id]\` — same `requireOwner()` guard.
- `.\web\app\admin\layout.tsx` — replace the "Sign out" form with a static "Signed in as {email} · sign out via Cloudflare" link to `/cdn-cgi/access/logout` (Cloudflare-provided).
- `.\web\app\admin\page.tsx` — leave as redirect to `/admin/inquiries`.

### D. Dashboard UX additions (minimal, scoped to existing page)

`.\web\app\admin\inquiries\page.tsx` is already a list view. Extend in-place (no new files):

- Add a small header strip: total / new / replied counts (computed from the array already loaded).
- Add a query-param filter `?status=new|replied|archived` (server-side filter on the existing `listInquiries()` result).
- Add a "Mark as read" form-action shortcut per row (POST to existing reply/status endpoint).
- Show `created_at` in `Europe/Zurich` for the owner's locale.

These are optional polish items; the security model is the primary objective.

### E. Robots & build hardening

- `.\web\app\admin\layout.tsx` already sets `robots: { index: false, follow: false }` — keep.
- Add a top-level `headers()` rule in `.\web\next.config.mjs` for any request whose host is the internal host: emit `X-Robots-Tag: noindex, nofollow` and `Cache-Control: private, no-store`. (Next's `headers()` cannot match host directly; instead apply to `/admin/:path*` and `/api/admin/:path*` — same effect because those paths only resolve on `ops.*` thanks to the middleware.)
- Add `Strict-Transport-Security`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy: ()` headers for the `/admin/:path*` matcher.

### F. Environment variables

New (set in deploy environment, not committed):

- `INTERNAL_HOST=ops.bettingwithai.app`
- `OWNER_EMAIL=marcel@bettingwithai.app` (single allow-listed identity)
- `CF_ACCESS_TEAM_DOMAIN=bettingwithai.cloudflareaccess.com`
- `CF_ACCESS_AUD=<application-AUD-tag-from-cloudflare>`

Remove (no longer used):

- `ADMIN_PASSWORD`
- `ADMIN_SESSION_SECRET`

Update `.\web\.env.local.example` to reflect this swap.

## Verification

1. **Type-check & lint**
   - `cd web`
   - `npm run lint`
   - `npm run type-check`

2. **Local smoke without Cloudflare** (dev mode bypass)
   - Add an `if (process.env.NODE_ENV !== 'production')` short-circuit in the JWT verifier that accepts a fake header `x-dev-owner: <email>` only when `ALLOW_DEV_OWNER=1`. Document this in the env example.
   - `INTERNAL_HOST=localhost:3001 npm run dev` on port 3001 (alongside `npm run dev` on 3000 for the public site).
   - Visit `http://localhost:3000/admin/inquiries` → expect 404 (public host blocks `/admin`).
   - Visit `http://localhost:3001/admin/inquiries` without dev header → expect "Access denied".
   - With `x-dev-owner: marcel@bettingwithai.app` → expect the inquiry list.

3. **Cloudflare staging**
   - Point `ops-staging.bettingwithai.app` at the staging origin via Tunnel.
   - Configure an Access app with WebAuthn-only policy.
   - Enroll a passkey + 2 YubiKeys.
   - Visit `https://ops-staging.bettingwithai.app/admin/inquiries` from a clean browser:
     - Expect Cloudflare Access challenge (WebAuthn).
     - After authenticating with a YubiKey → land on the dashboard.
     - Confirm `Cf-Access-Jwt-Assertion` header is present in origin logs and the `email` claim equals `OWNER_EMAIL`.
   - Try `https://ops-staging.bettingwithai.app/some/random/path` → 404 from app (not 200).
   - Try `https://bettingwithai.app/admin/inquiries` → 404 (middleware blocks).

4. **Negative tests**
   - Remove the YubiKeys from the Access policy → next login attempt must fail at the Access step (no passkey == no entry).
   - Forge a JWT with valid structure but wrong `aud` → middleware returns 403.
   - Send request directly to origin bypassing Cloudflare (only possible if Tunnel is not used; if direct origin is reachable, add a Cloudflare-only IP allow-list at the origin's reverse proxy / Railway).

5. **Public surface check**
   - `curl -I https://bettingwithai.app/admin` → expect 404, not 401/302.
   - `curl -I https://bettingwithai.app/admin/login` → expect 404 (page deleted).
   - Page-source of public site must contain no string `admin` in nav or footer.

## Files modified / created (summary)

Modify:
- `.\web\middleware.ts` (host-aware routing + JWT pre-check)
- `.\web\next.config.mjs` (security headers for `/admin/:path*`)
- `.\web\app\admin\layout.tsx` (replace sign-out with Cloudflare logout link)
- `.\web\app\admin\inquiries\page.tsx` (`requireOwner()`, optional polish)
- `.\web\app\admin\inquiries\[id]\page.tsx` (`requireOwner()`)
- `.\web\app\api\admin\inquiries\[id]\…` (any route handlers — `requireOwner()`)
- `.\web\.env.local.example`

Create:
- `.\web\lib\accessAuth.ts` (CF Access JWT verification + `requireOwner()`)

Delete:
- `.\web\app\admin\login\page.tsx`
- `.\web\app\api\admin\login\route.ts`
- `.\web\app\api\admin\logout\route.ts`
- `.\web\components\AdminLoginForm.tsx`
- `.\web\lib\adminAuth.ts`

Out-of-repo (Cloudflare dashboard) — operator checklist:
1. Add `ops.bettingwithai.app` DNS (proxied) or expose via `cloudflared` Tunnel.
2. Create a Self-hosted Access app on that hostname.
3. Policy: `Allow` if `email == OWNER_EMAIL` AND `auth_method == webauthn`.
4. Disable email-OTP fallback; keep only WebAuthn IdP / WebAuthn-required policy.
5. Enroll passkey + 2 FIDO2 keys.
6. Copy the application AUD tag → set as `CF_ACCESS_AUD` env.
7. Set `CF_ACCESS_TEAM_DOMAIN` to `<team>.cloudflareaccess.com`.

## Result

- Attackers on the public origin literally cannot find `/admin` (404) and there is no login form anywhere on `www`/apex.
- Attackers who guess `ops.bettingwithai.app` are stopped at Cloudflare Access; the origin never sees their request when Cloudflare Tunnel is used.
- Even if they reach the origin, the middleware rejects requests without a valid CF Access JWT.
- The only credential that grants access is a Passkey or one of the two FIDO2 hardware keys bound to the owner's identity — phishing-resistant and not stored in our app.
