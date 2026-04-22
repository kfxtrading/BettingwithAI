'use client';

import Link from 'next/link';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';
import { RailQuickLinks } from './RailQuickLinks';
import { RailSpaces } from './RailSpaces';
import { RailTodayFeed } from './RailTodayFeed';

export function LeftRail() {
  const { href, locale } = useLocale();

  return (
    <aside
      aria-label="Sidebar"
      className="sticky top-0 hidden h-screen shrink-0 flex-col gap-5 border-r border-black/5 bg-surface/60 px-3 py-5 backdrop-blur supports-[backdrop-filter]:bg-surface/50 lg:flex dark:border-white/5"
    >
      <Link
        href={href('/')}
        hrefLang={locale}
        className="focus-ring flex items-baseline gap-2 px-3 text-base font-medium tracking-tight"
      >
        <span className="inline-block h-2 w-2 rounded-full bg-accent" />
        Betting with AI
      </Link>

      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto">
        <RailQuickLinks />
        <RailSpaces />
        <RailTodayFeed />
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-black/5 pt-3 dark:border-white/5">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>
    </aside>
  );
}
