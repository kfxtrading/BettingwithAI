# Plan: Mobile Optimization for LanguageSwitcher & CookieConsent

## Problem

On mobile viewports:

1. **LanguageSwitcher** (`web/components/LanguageSwitcher.tsx`) renders `<option>` text as
   `DE · Deutsch`, `EN · English`, `FR · Français`, ... The native `<select>` sizes
   itself to its widest option, so the collapsed control is wider than needed and
   overflows the header. This triggers a horizontal scrollbar on the whole page.
2. **CookieConsent** (`web/components/CookieConsent.tsx`) sits inside that
   horizontally scrollable viewport, so content visually appears cut off on the
   right. The dialog itself is also too tall on small screens when the details
   panel is open.

## Root cause of horizontal scroll

The `<select>` intrinsic width grows with the longest option. Tailwind classes
on the select (`px-3 py-1.5 pr-7 text-xs`) plus the Nav layout
(`gap-8` between the logo block and the links block, plus three rounded link
pills) push total width past 375px on small phones. There is no `overflow-x`
clipping on `<html>/<body>` or the Nav container, so the page scrolls sideways.

## Goal

Eliminate horizontal overflow and make the cookie banner fully visible on mobile
without losing the language selection UX on larger screens.

## Design

### 1. `web/components/LanguageSwitcher.tsx`

- Keep the native `<select>` (accessible, no extra JS).
- Render **two option label variants**:
  - Mobile (`< sm`): just the uppercase locale code (`DE`, `EN`, ...).
  - `sm+`: the current long form `DE · Deutsch`.
- Detect viewport with a small `useIsMobile()` hook based on
  `window.matchMedia('(max-width: 639px)')` (tailwind `sm` breakpoint = 640px).
  Initialise to `false` to avoid hydration mismatch, update in `useEffect`.
- Tighten the collapsed control on mobile: `px-2 pr-6` instead of `px-3 pr-7`.
- Keep the `▾` caret but shift it to `right-1.5` on mobile.

No changes to `lib/i18n/locales.ts` — labels stay intact; only the rendered
option text changes.

### 2. `web/components/Nav.tsx`

- Reduce the flex gap on mobile so the header never exceeds viewport width:
  change `gap-8` → `gap-3 md:gap-8`.
- Add `min-w-0` to the `<nav>` wrapper so its children can shrink.
- No other structural changes (links remain visible, switch still inline).

### 3. `web/components/CookieConsent.tsx`

- Container already uses `fixed inset-x-0 bottom-0 px-4 pb-4`. Keep that, but:
  - On mobile reduce inner padding: `p-4 md:p-6` (from `p-5 md:p-6`).
  - Cap height so long German/French copy scrolls inside the card:
    add `max-h-[85vh] overflow-y-auto` on the inner card wrapper.
  - Switch the action row to full-width stacked buttons on mobile while
    keeping the wrap layout on `sm+`: use
    `flex-col sm:flex-row sm:flex-wrap sm:justify-end` and give each button
    `w-full sm:w-auto justify-center`.
  - Slightly smaller title on mobile: `text-sm md:text-base`.
- No logic changes (consent persistence untouched).

### 4. Optional safety net (globals.css)

Not needed if the above fixes the intrinsic width issue. Skipping to keep the
change minimal.

## Files to modify

- `web/components/LanguageSwitcher.tsx`
- `web/components/Nav.tsx`
- `web/components/CookieConsent.tsx`

## Verification

1. `cd web && npm run lint && npm run type-check`
2. `cd web && npm run dev` and open the site on a 360–390px wide viewport
   (Chrome DevTools device mode, iPhone SE):
   - Header fits with no horizontal scroll.
   - Language switcher shows only `DE` / `EN` etc.; dropdown open still shows
     long names (native mobile select UI renders the option text which is now
     short — acceptable per user request).
   - Cookie banner fully visible, buttons stack vertically, `Accept all` is
     reachable without horizontal scroll. Toggle "Einstellungen" — details
     panel scrolls inside the card.
3. Re-test at `sm` (640px+) — original desktop layout is preserved.
