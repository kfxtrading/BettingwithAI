# Plan: Support Chatbot (Collapsible Right-Anchored Widget)

## Goal
Add a support feature that answers the most common FAQs. UI: a collapsible bar anchored to the bottom-right of every page (the currently free right-hand area). Clicking the bar expands a chat panel upward; the user can pick suggested questions or type their own, and the bot returns the best-matching answer.

## Approach
**Frontend-only** with static FAQ data and `fuse.js` fuzzy search.

Justification:
- FAQ content is small, static, and non-sensitive — no need for a backend round-trip.
- Zero backend changes → smaller blast radius, faster iteration, independently deployable.
- `fuse.js` is ~15 KB, zero transitive deps. Only new dependency.
- Testable with a trivial unit test on `searchFaq()` if desired.

A backend endpoint (`POST /support/ask`) was considered but rejected: it adds a new FastAPI route, Pydantic schemas, a pytest fixture, and network latency — without meaningfully improving answer quality for a tiny static FAQ set.

## Files to Create / Edit

### New
| File | Purpose |
|---|---|
| `web/lib/faq.ts` | FAQ dataset (i18n-aware via translation keys) + `searchFaq()` using `fuse.js` |
| `web/components/SupportChat.tsx` | Floating collapsible chat widget (client component) |

### Edit
| File | Change |
|---|---|
| `web/package.json` | Add `fuse.js` dependency |
| `web/app/layout.tsx` | Import and mount `<SupportChat />` once (below `<CookieConsent />`) so it appears on every page/locale |
| `web/lib/i18n/en.ts` | Add `support.*` keys to union + English values |
| `web/lib/i18n/de.ts` | German values |
| `web/lib/i18n/es.ts` | Spanish values |
| `web/lib/i18n/fr.ts` | French values |
| `web/lib/i18n/it.ts` | Italian values |

No backend changes. No test file needed (optional: `web/lib/__tests__/faq.test.ts` later).

## Component Design (`SupportChat.tsx`)

- Fixed position: `bottom-4 right-4 z-50`.
- **Collapsed state**: pill-style bar `surface` background + `border-border` + `shadow-soft`, icon `MessageCircle` (lucide-react) + label `t('support.toggle.label')`.
- **Expanded state**: `360×480 px` dialog (`role="dialog"`, `aria-modal="true"`, `aria-label`) with:
  - Header: panel title + close (X) button.
  - Body (scrollable):
    - When message list is empty → show `suggestions.heading` + 5 clickable FAQ buttons (seed questions).
    - Otherwise → alternating user/bot bubbles (user: `bg-accent text-white ml-auto`, bot: `bg-surface-2`).
  - Footer: text input + send button. Enter key submits.
- Animation: `framer-motion` `AnimatePresence` + `motion.div` for expand/collapse (already installed).
- Accessibility: `aria-expanded`, `aria-controls`, `useId` for panel ID, autofocus input on open, `bottomRef.scrollIntoView` for auto-scroll.
- Styling: reuse existing utilities `surface-card` / `focus-ring` / `press` where appropriate; use existing Tailwind design tokens (`surface`, `surface-2`, `border`, `text`, `muted`, `accent`).

## FAQ Data (`web/lib/faq.ts`)

Structure:
```ts
export interface FaqEntry {
  id: string;
  questionKey: DictionaryKey; // i18n key for the question text
  answerKey: DictionaryKey;   // i18n key for the answer text
  tags: string[];             // English tags used for fuzzy matching
}
```

Include ~8–10 seed entries covering common topics:
- What is a value bet? / What is "edge" / Kelly staking?
- How accurate are the predictions? (models, RPS)
- Where does the data come from? (Football-Data CSVs, Sofascore opt-in)
- How often is the snapshot updated?
- What does the performance tracker show?
- What is Pi-Rating?
- Is this financial advice / responsible gambling disclaimer?
- How do I change the language?
- How do I withdraw cookie consent?

`searchFaq(query: string, t)`:
- Build a `Fuse` instance over `[{ id, question: t(questionKey), tags }]` on each call (cheap, entries are few) OR once per locale via memo.
- Threshold `0.45`, `includeScore: true`, top 4 results.
- Return `{ entry, score }[]`.

Bot reply logic:
- If best result score ≤ ~0.55 → return `t(entry.answerKey)`.
- Else → return `t('support.fallback')`.

## i18n Keys to Add

```
support.toggle.label          # "Hilfe / Support" (de), "Help / Support" (en) …
support.panel.title           # "Support-Chat"
support.panel.close           # aria-label for close button
support.input.placeholder     # "Frage stellen…"
support.input.send            # aria-label for send button
support.suggestions.heading   # "Häufige Fragen"
support.fallback              # "Keine passende Antwort gefunden. Formuliere die Frage neu oder kontaktiere uns."
support.faq.{id}.q            # one per FAQ entry — question text
support.faq.{id}.a            # one per FAQ entry — answer text
```

All 5 locale files (`en.ts`, `de.ts`, `es.ts`, `fr.ts`, `it.ts`) must be updated consistently to keep the `DictionaryKey` union exhaustive (strict typing).

## Layout Integration

Edit `web/app/layout.tsx`: import `SupportChat`, render inside the existing providers tree below `<CookieConsent />` (fixed-position siblings, no layout flow impact). The widget is rendered once globally and appears on every page/locale.

## Verification

```bash
# Install dep
cd web && npm install fuse.js

# Type + lint
cd web && npm run lint && npm run type-check

# Dev run
cd web && npm run dev    # → http://localhost:3000
```

Manual checks:
1. Bar visible bottom-right on the home page, value-bets page, performance, leagues, legal pages.
2. Click → panel expands smoothly; suggested FAQs are clickable and produce bot answers inline.
3. Typing a known phrase (e.g. "value bet") returns the correct answer.
4. Typing gibberish returns `support.fallback`.
5. Escape/X closes the panel; focus returns to the toggle button.
6. Switch locale (language switcher in nav) → labels + FAQ content translate.
7. Cookie consent modal and support bar do not overlap visually (CookieConsent is typically bottom-left/center or on close; stack order via z-index already `z-50`).

## Non-Goals / Deferred
- LLM/RAG-based answers (future: optional `/support/ask` endpoint calling Azure OpenAI).
- Message history persistence.
- Agent handoff / human support tickets.
- Analytics events for FAQ hits.
