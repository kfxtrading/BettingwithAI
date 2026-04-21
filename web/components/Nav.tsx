'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { stripLocale } from '@/lib/seo';
import type { DictionaryKey } from '@/lib/i18n';
import { LanguageSwitcher } from './LanguageSwitcher';

const BREADCRUMB_LABELS: Record<string, DictionaryKey> = {
  performance: 'nav.performance',
  leagues: 'nav.leagues',
  learn: 'rail.quick.learn',
};

function humanize(segment: string): string {
  return segment
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function Nav() {
  const pathname = usePathname();
  const { t, locale, href } = useLocale();
  const localePathname = stripLocale(pathname ?? '/');

  const mobileLinks = [
    { path: '/', label: t('nav.today') },
    { path: '/performance', label: t('nav.performance') },
    { path: '/leagues', label: t('nav.leagues') },
  ];

  const segments = localePathname.split('/').filter(Boolean);

  return (
    <header className="sticky top-0 z-30 border-b border-transparent bg-bg/80 backdrop-blur supports-[backdrop-filter]:bg-bg/60">
      <div className="mx-auto flex w-full max-w-page items-center justify-between gap-3 px-4 py-4 sm:px-6 md:gap-8 md:px-12">
        {/* Mobile: logo + primary links */}
        <div className="flex items-center gap-3 lg:hidden">
          <Link
            href={href('/')}
            hrefLang={locale}
            className="focus-ring flex items-baseline gap-2 text-base font-medium tracking-tight"
          >
            <span className="inline-block h-2 w-2 rounded-full bg-accent" />
            Betting with AI
          </Link>
        </div>

        <nav className="flex min-w-0 items-center gap-1 text-sm lg:hidden">
          {mobileLinks.map((link) => {
            const active =
              link.path === '/'
                ? localePathname === '/'
                : localePathname.startsWith(link.path);
            return (
              <Link
                key={link.path}
                href={href(link.path)}
                hrefLang={locale}
                className={`focus-ring press rounded-full px-3.5 py-1.5 transition-colors ease-ease ${
                  active
                    ? 'bg-surface text-text shadow-soft'
                    : 'text-muted hover:text-text'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Desktop: breadcrumb */}
        <nav
          aria-label="Breadcrumb"
          className="hidden min-w-0 flex-1 items-center gap-2 text-sm lg:flex"
        >
          <Link
            href={href('/')}
            hrefLang={locale}
            className={`focus-ring rounded-md px-1 ${
              segments.length === 0
                ? 'text-text'
                : 'text-muted hover:text-text'
            }`}
          >
            {t('breadcrumb.home')}
          </Link>
          {segments.map((seg, i) => {
            const isLast = i === segments.length - 1;
            const pathTo = '/' + segments.slice(0, i + 1).join('/');
            const labelKey = BREADCRUMB_LABELS[seg];
            const label = labelKey ? t(labelKey) : humanize(decodeURIComponent(seg));
            return (
              <span
                key={pathTo}
                className="flex min-w-0 items-center gap-2 text-muted"
              >
                <span aria-hidden className="text-muted/60">
                  /
                </span>
                {isLast ? (
                  <span className="truncate text-text">{label}</span>
                ) : (
                  <Link
                    href={href(pathTo)}
                    hrefLang={locale}
                    className="focus-ring truncate rounded-md px-1 hover:text-text"
                  >
                    {label}
                  </Link>
                )}
              </span>
            );
          })}
        </nav>

        <div className="flex items-center lg:hidden">
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
