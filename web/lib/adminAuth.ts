import { cookies } from 'next/headers';
import { createHmac, timingSafeEqual } from 'node:crypto';
import type { NextRequest } from 'next/server';

export const ADMIN_COOKIE = 'bw_admin';
export const ADMIN_COOKIE_MAX_AGE = 60 * 60 * 12; // 12h

function adminSecret(): string {
  return (
    process.env.ADMIN_SESSION_SECRET ??
    'betting-with-ai-admin-secret-change-me'
  );
}

function adminPassword(): string {
  return process.env.ADMIN_PASSWORD ?? '';
}

export function expectedSessionToken(): string {
  const pw = adminPassword();
  if (!pw) return '';
  return createHmac('sha256', adminSecret()).update(pw).digest('hex');
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  try {
    return timingSafeEqual(Buffer.from(a), Buffer.from(b));
  } catch {
    return false;
  }
}

/** Returns true iff ADMIN_PASSWORD is set AND the submitted value matches. */
export function verifyPassword(input: string): boolean {
  const pw = adminPassword();
  if (!pw) return false;
  return safeEqual(input, pw);
}

/** Check auth for Server Components via `cookies()`. */
export function isAdminAuthenticated(): boolean {
  const expected = expectedSessionToken();
  if (!expected) return false;
  const got = cookies().get(ADMIN_COOKIE)?.value ?? '';
  return safeEqual(got, expected);
}

/** Check auth for Route Handlers / Middleware via request cookies. */
export function isAdminAuthenticatedReq(req: NextRequest): boolean {
  const expected = expectedSessionToken();
  if (!expected) return false;
  const got = req.cookies.get(ADMIN_COOKIE)?.value ?? '';
  return safeEqual(got, expected);
}
