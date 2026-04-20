'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  BookOpen,
  LayoutGrid,
  Sparkles,
  Trophy,
  type LucideIcon,
} from 'lucide-react';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { stripLocale } from '@/lib/seo';
import type { DictionaryKey } from '@/lib/i18n';

type Item = {
  path: string;
  labelKey: DictionaryKey;
  Icon: LucideIcon;
};

const items: Item[] = [
  { path: '/', labelKey: 'nav.today', Icon: Sparkles },
  { path: '/performance', labelKey: 'nav.performance', Icon: BarChart3 },
  { path: '/leagues', labelKey: 'nav.leagues', Icon: Trophy },
  { path: '/track-record', labelKey: 'rail.quick.trackRecord', Icon: LayoutGrid },
  { path: '/learn', labelKey: 'rail.quick.learn', Icon: BookOpen },
];

export function RailQuickLinks() {
  const pathname = usePathname() ?? '/';
  const { t, locale, href } = useLocale();
  const localePath = stripLocale(pathname);

  return (
    <nav
      aria-label={t('rail.section.explore')}
      className="flex flex-col gap-0.5"
    >
      <div className="px-3 pb-1.5 pt-1 text-2xs uppercase tracking-[0.12em] text-muted">
        {t('rail.section.explore')}
      </div>
      {items.map(({ path, labelKey, Icon }) => {
        const active =
          path === '/'
            ? localePath === '/'
            : localePath.startsWith(path);
        return (
          <Link
            key={path}
            href={href(path)}
            hrefLang={locale}
            className={`focus-ring press group flex items-center gap-2.5 rounded-lg px-3 py-1.5 text-sm transition-colors ease-ease ${
              active
                ? 'bg-surface text-text shadow-soft'
                : 'text-muted hover:bg-surface-2 hover:text-text'
            }`}
          >
            <Icon
              size={16}
              strokeWidth={1.75}
              className={active ? 'text-accent' : ''}
              aria-hidden
            />
            <span className="truncate">{t(labelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
