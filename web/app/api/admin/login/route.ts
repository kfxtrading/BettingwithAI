import { NextResponse, type NextRequest } from 'next/server';
import {
  ADMIN_COOKIE,
  ADMIN_COOKIE_MAX_AGE,
  expectedSessionToken,
  verifyPassword,
} from '@/lib/adminAuth';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  let body: { password?: unknown };
  try {
    body = (await request.json()) as { password?: unknown };
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }
  const password = typeof body.password === 'string' ? body.password : '';
  if (!verifyPassword(password)) {
    return NextResponse.json({ error: 'invalid' }, { status: 401 });
  }

  const token = expectedSessionToken();
  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: ADMIN_COOKIE_MAX_AGE,
  });
  return res;
}
