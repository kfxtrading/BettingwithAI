import { NextResponse, type NextRequest } from 'next/server';
import { ADMIN_COOKIE } from '@/lib/adminAuth';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function clearAndRedirect(request: NextRequest) {
  const target = new URL('/admin/login', request.url);
  const res = NextResponse.redirect(target, 303);
  res.cookies.set(ADMIN_COOKIE, '', {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 0,
  });
  return res;
}

export async function POST(request: NextRequest) {
  return clearAndRedirect(request);
}

export async function GET(request: NextRequest) {
  return clearAndRedirect(request);
}
