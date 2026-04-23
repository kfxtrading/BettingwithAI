# Plan — Investor inquiries section

## Goal
Add a small, sober "Investor inquiries" presence on the Betting with AI site:
- A discreet footer link (no top-nav entry) pointing at a short teaser page.
- A short editorial-style `/investors` page with headline, 2–3 sentences, 3 mini-blocks and one CTA.
- A simple, vor-qualifizierendes contact form (`/investors/contact`) that POSTs to a new API route which emails the founder (and rate-limits).
- No public pitch deck, no financial figures, no 15-field form.

## Non-goals
- Not adding a top-nav "Investors" item (pollutes primary nav). Footer-only is enough and matches private AI-startup patterns.
- No dashboard, no investor login, no file hosting.
- No changes to Python backend. Everything lives in `web/`.

## Architecture overview

```
Footer "Investors" link
        │
        ▼
/[locale]/investors/page.tsx          ← teaser (EditorialPage)
        │ CTA
        ▼
/[locale]/investors/contact/page.tsx  ← form page (server component wrapping client form)
        │ submit
        ▼
POST /api/investors                   ← validates + emails founder
```

## Files to create

### 1. Teaser page
`web/app/[locale]/investors/page.tsx`
- Uses existing `EditorialPage` component (same pattern as `impressum`, `responsible-gambling`).
- Sections:
  1. Intro paragraph (i18n `page.investors.intro`).
  2. Three mini-blocks: **Product**, **Market**, **Stage** — short one-liners each.
  3. CTA button → `/investors/contact` (primary) and mailto fallback (`investors@bettingwithai.app`).
- Metadata: `robots: { index: false, follow: true }` (we don't want SEO competition for this page; it's a back-channel).
- Schema `WebPage`.
- `lastUpdated` constant (manual bump like other legal pages).

### 2. Contact / form page
`web/app/[locale]/investors/contact/page.tsx` (server component for metadata + schema)
- Renders `<InvestorInquiryForm />` (new client component).
- Metadata: `robots: { index: false, follow: false }`.

`web/components/InvestorInquiryForm.tsx` (new, `'use client'`)
- Fields (exactly 6, keep minimal):
  - `name` (required)
  - `company` (required) — Company / Fund
  - `email` (required, type=email)
  - `check_size` (optional, free text: "Check size or investment focus")
  - `region` (optional)
  - `message` (required, textarea)
- Honeypot hidden field `website` to deter bots.
- Client-side validation (simple required + email regex). Submit state: idle / submitting / sent / error.
- On success renders a confirmation block (no redirect, simpler UX).
- Styling: matches `EditorialPage` prose container + existing `surface-card` / `focus-ring` utility classes seen across components.
- Uses `useLocale()` for labels (same pattern as `SupportChat`, `RecentBets`).

### 3. API route
`web/app/api/investors/route.ts`
- `POST` handler, `dynamic = 'force-dynamic'`.
- Validates JSON body (shape guard, trim, length caps ~2000 chars, email regex).
- Rejects if honeypot `website` is non-empty (silent 200 to fool bots).
- In-memory IP rate limit (5/hour per IP, Map keyed by `x-forwarded-for`; same light-weight approach used elsewhere in the web app).
- Sends email via SMTP if env vars are set; otherwise logs to server console and returns 202 (so dev works without SMTP).
  - Env: `INVESTOR_INQUIRY_TO`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`.
  - Use `nodemailer` if already a dep; if not, use built-in `fetch` against a generic SMTP HTTP bridge is **not** desirable — so fall back to a small no-dep approach: POST to `MAIL_WEBHOOK_URL` if set, otherwise just log. (Chosen to avoid introducing new deps; final choice confirmed after checking `web/package.json`.)
- Returns `{ ok: true }` on success, `{ error }` on failure with appropriate status.

### 4. Footer link
Edit `web/components/Footer.tsx`:
- Extend `FooterLink.labelKey` union with `'footer.link.investors'`.
- Add a 4th column or append into the existing "Product" column header — cleanest is a **new column** under header `footer.col.company` containing a single `Investor inquiries` link. The grid currently `md:grid-cols-3`; bump to `md:grid-cols-4`.
- Alternative (considered but rejected): only the existing "Product" column, since the user explicitly mentioned the footer as preferred placement and "Investors" is not a product. A small dedicated "Company" column is the cleanest fit.

### 5. i18n keys (all 5 locales: `en`, `de`, `fr`, `it`, `es`)
Add to the `DictionaryKey` union and each dictionary object in:
`web/lib/i18n/en.ts`, `de.ts`, `fr.ts`, `it.ts`, `es.ts`.

New keys:
- `footer.col.company`
- `footer.link.investors`
- `page.investors.title`
- `page.investors.description`
- `page.investors.intro`
- `page.investors.block.product.title`
- `page.investors.block.product.body`
- `page.investors.block.market.title`
- `page.investors.block.market.body`
- `page.investors.block.stage.title`
- `page.investors.block.stage.body`
- `page.investors.cta.requestAccess`
- `page.investors.cta.email`
- `page.investors.contact.title`
- `page.investors.contact.description`
- `page.investors.contact.intro`
- `page.investors.form.name`
- `page.investors.form.company`
- `page.investors.form.email`
- `page.investors.form.checkSize`
- `page.investors.form.region`
- `page.investors.form.message`
- `page.investors.form.submit`
- `page.investors.form.submitting`
- `page.investors.form.success.title`
- `page.investors.form.success.body`
- `page.investors.form.error.generic`
- `page.investors.form.error.validation`

Start with faithful English copy, then translate to DE/FR/IT/ES (short, formal tone — match existing dictionaries).

### 6. Sitemap
Edit `web/app/sitemap.ts`:
- `/investors` is `noindex`, therefore **excluded** from the sitemap (follow the pattern of `/legal/cookies` which is intentionally excluded). Add a comment noting this.
- `/investors/contact` likewise excluded.

### 7. Nav (no change)
`web/components/Nav.tsx` — no changes. `BREADCRUMB_LABELS` optionally gains `investors: 'footer.link.investors'` so the breadcrumb reads "Investor inquiries" on the page. Small, safe tweak.

## Copy (initial, English)

**Teaser (page.investors.intro):**
> Betting with AI is building an AI-powered football intelligence platform focused on predictions, data-driven insights and premium subscription products. We welcome conversations with strategic investors and operators experienced in sports, AI, consumer products and subscription businesses.

**Blocks:**
- Product — *AI-driven football insights and prediction infrastructure.*
- Market — *Scalable consumer and premium data products across European football.*
- Stage — *Currently building traction, product and early investor conversations.*

**CTA:** `Request investor information` → `/investors/contact`
Secondary: `investors@bettingwithai.app`

## Verification

1. **Type-check & lint**
   ```bash
   cd web
   npm run type-check
   npm run lint
   ```
   Must pass cleanly — all new dictionary keys present in every locale (strict TS union will fail otherwise).

2. **Runtime smoke**
   ```bash
   cd web
   npm run dev
   ```
   - Visit `http://localhost:3000/en/investors` — teaser renders, CTA present.
   - Visit `/de/investors`, `/fr/investors`, `/it/investors`, `/es/investors` — all localized.
   - Click CTA → `/en/investors/contact` shows form.
   - Submit empty form → validation messages.
   - Submit valid form without SMTP env → 202, success UI; check server log for the payload.
   - Submit with honeypot filled (via devtools) → silent 200, no log.
   - Spam-submit 6× from same IP → last one returns 429.
   - `view-source:` of `/en/investors` contains `<meta name="robots" content="noindex, follow">`.
   - Footer shows new "Investor inquiries" link in the 4th column on desktop.

3. **Sitemap sanity**
   ```bash
   curl http://localhost:3000/sitemap.xml | grep -i investors
   ```
   Expect no matches.

## Files modified / created (summary)

Created:
- `web/app/[locale]/investors/page.tsx`
- `web/app/[locale]/investors/contact/page.tsx`
- `web/components/InvestorInquiryForm.tsx`
- `web/app/api/investors/route.ts`

Modified:
- `web/components/Footer.tsx`
- `web/components/Nav.tsx` (optional breadcrumb label)
- `web/lib/i18n/en.ts`, `de.ts`, `fr.ts`, `it.ts`, `es.ts`
- `web/app/sitemap.ts` (comment only, optional)
