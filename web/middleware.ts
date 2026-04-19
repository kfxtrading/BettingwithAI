import { NextResponse, type NextRequest } from 'next/server';
import { defaultLocale, locales, type Locale } from '@/lib/i18n';

const LOCALE_COOKIE = 'NEXT_LOCALE';
const ONE_YEAR = 60 * 60 * 24 * 365;

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

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Detect a leading "/<locale>" segment in the URL.
  const firstSegment = pathname.split('/')[1] ?? '';
  const urlLocale = isLocale(firstSegment) ? firstSegment : null;

  // (1) URL has a locale prefix -> propagate locale via header + cookie.
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

  // (2) URL has no locale prefix -> redirect to /<locale>/<rest>.
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
  // Skip Next internals, API routes, files with a dot (assets), and known
  // SEO files served by route handlers / static files.
  matcher: [
    '/((?!_next/|api/|llms\\.txt|robots\\.txt|sitemap\\.xml|sitemaps/|favicon\\.ico|.*\\..*).*)',
  ],
};
