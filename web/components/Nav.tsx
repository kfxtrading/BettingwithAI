'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { stripLocale } from '@/lib/seo';
import { LanguageSwitcher } from './LanguageSwitcher';

export function Nav() {
  const pathname = usePathname();
  const { t, locale, href } = useLocale();
  const localePathname = stripLocale(pathname ?? '/');

  const links = [
    { path: '/', label: t('nav.today') },
    { path: '/performance', label: t('nav.performance') },
    { path: '/leagues', label: t('nav.leagues') },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-transparent bg-bg/80 backdrop-blur supports-[backdrop-filter]:bg-bg/60">
      <div className="mx-auto flex w-full max-w-page items-center justify-between gap-8 px-6 py-4 md:px-12">
        <Link
          href={href('/')}
          hrefLang={locale}
          className="focus-ring flex items-baseline gap-2 text-base font-medium tracking-tight"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-accent" />
          Betting with AI
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {links.map((link) => {
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
          <LanguageSwitcher />
        </nav>
      </div>
    </header>
  );
}
