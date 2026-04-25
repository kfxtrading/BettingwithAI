import { NextResponse, type NextRequest } from 'next/server';
import { defaultLocale, locales, type Locale } from '@/lib/i18n';

const LOCALE_COOKIE = 'NEXT_LOCALE';
const ONE_YEAR = 60 * 60 * 24 * 365;

const CANONICAL_HOST = process.env.CANONICAL_HOST ?? 'bettingwithai.app';
const INTERNAL_HOST = (
  process.env.INTERNAL_HOST ?? 'ops.bettingwithai.app'
).toLowerCase();
const FORCE_HTTPS =
  (process.env.FORCE_HTTPS ?? (process.env.NODE_ENV === 'production' ? '1' : '0')) === '1';

function isLocale(value: string | undefined): value is Locale {
  return !!value && (locales as readonly string[]).includes(value);
}

function detectLocale(request: NextRequest): Locale {
  const cookie = request.cookies.get(LOCALE_COOKIE)?.value;
  if (isLocale(cookie)) return cookie;
  const accept = request.headers.get('accept-language');
  if (accept) {
    for (const part of accept.split(',')) {
      const tag = part.split(';')[0].trim().toLowerCase().slice(0, 2);
      if (isLocale(tag)) return tag;
    }
  }
  return defaultLocale;
}

function isInternalHostname(hostname: string): boolean {
  if (!hostname) return false;
  if (hostname === INTERNAL_HOST) return true;
  // Allow localhost for local dev of the internal site on a separate port.
  if (
    process.env.NODE_ENV !== 'production' &&
    (hostname === 'localhost' || hostname === '127.0.0.1') &&
    process.env.DEV_INTERNAL === '1'
  ) {
    return true;
  }
  return false;
}

function notFound(_request: NextRequest): NextResponse {
  return new NextResponse('Not found', {
    status: 404,
    headers: { 'content-type': 'text/plain; charset=utf-8' },
  });
}

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const forwardedHost = request.headers.get('x-forwarded-host');
  const forwardedProto = request.headers.get('x-forwarded-proto');
  const host = forwardedHost ?? request.headers.get('host') ?? '';
  const proto = forwardedProto ?? request.nextUrl.protocol.replace(':', '');
  const hostname = host.split(':')[0].toLowerCase();
  const onInternal = isInternalHostname(hostname);

  // (0a) HTTPS upgrade applies to everything in production.
  if (FORCE_HTTPS && proto === 'http') {
    const target = new URL(request.nextUrl.toString());
    target.protocol = 'https:';
    return NextResponse.redirect(target, 308);
  }

  // (0b) Canonical-host redirect ONLY for the public site. Never rewrite
  // the internal hostname.
  if (!onInternal && hostname === `www.${CANONICAL_HOST}`) {
    const target = new URL(request.nextUrl.toString());
    target.host = CANONICAL_HOST;
    return NextResponse.redirect(target, 308);
  }

  // (0c) HEAD short-circuit (uptime probes).
  if (request.method === 'HEAD') {
    return NextResponse.next();
  }

  // ── Internal host (dashboard) ────────────────────────────────────────
  if (onInternal) {
    // Allow only admin surfaces on the internal hostname. Everything else
    // returns a 404 so the internal origin reveals nothing about the
    // public site.
    const allowed =
      pathname === '/' ||
      pathname.startsWith('/admin') ||
      pathname.startsWith('/api/admin') ||
      pathname === '/healthz' ||
      pathname.startsWith('/_next/');
    if (!allowed) {
      return notFound(request);
    }
    if (pathname === '/') {
      const url = request.nextUrl.clone();
      url.pathname = '/admin/inquiries';
      return NextResponse.redirect(url, 307);
    }
    return NextResponse.next();
  }

  // ── Public host ──────────────────────────────────────────────────────
  // Hide /admin entirely from the public origin: 404 instead of 302.
  if (pathname.startsWith('/admin') || pathname.startsWith('/api/admin')) {
    return notFound(request);
  }

  const firstSegment = pathname.split('/')[1] ?? '';
  const urlLocale = isLocale(firstSegment) ? firstSegment : null;

  if (urlLocale) {
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('x-locale', urlLocale);
    const response = NextResponse.next({ request: { headers: requestHeaders } });
    if (request.cookies.get(LOCALE_COOKIE)?.value !== urlLocale) {
      response.cookies.set(LOCALE_COOKIE, urlLocale, {
        path: '/',
        sameSite: 'lax',
        maxAge: ONE_YEAR,
      });
    }
    return response;
  }

  const locale = detectLocale(request);
  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname === '/' ? '' : pathname}`;
  url.search = search;
  const response = NextResponse.redirect(url, 308);
  response.cookies.set(LOCALE_COOKIE, locale, {
    path: '/',
    sameSite: 'lax',
    maxAge: ONE_YEAR,
  });
  return response;
}

export const config = {
  // Include /admin and /api/admin so the host-gate runs for those paths.
  // Skip Next internals and static assets.
  matcher: [
    '/((?!_next/|healthz|llms\\.txt|robots\\.txt|sitemap\\.xml|sitemaps/|favicon\\.ico|icon|apple-icon|.*\\..*).*)',
  ],
};
