'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { LanguageSwitcher } from './LanguageSwitcher';

export function Nav() {
  const pathname = usePathname();
  const { t } = useLocale();

  const links = [
    { href: '/', label: t('nav.today') },
    { href: '/performance', label: t('nav.performance') },
    { href: '/leagues', label: t('nav.leagues') },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-transparent bg-bg/80 backdrop-blur supports-[backdrop-filter]:bg-bg/60">
      <div className="mx-auto flex w-full max-w-page items-center justify-between gap-8 px-6 py-4 md:px-12">
        <Link
          href="/"
          className="focus-ring flex items-baseline gap-2 text-base font-medium tracking-tight"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-accent" />
          Betting with AI
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {links.map((link) => {
            const active =
              link.href === '/'
                ? pathname === '/'
                : pathname?.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
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
