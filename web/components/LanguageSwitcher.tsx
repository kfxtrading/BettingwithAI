'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { localeLabels, type Locale } from '@/lib/i18n';
import { localizedPath, stripLocale } from '@/lib/seo';

function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(max-width: 639px)');
    const update = (): void => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);
  return isMobile;
}

export function LanguageSwitcher() {
  const { locale, setLocale, availableLocales, t } = useLocale();
  const router = useRouter();
  const pathname = usePathname() ?? '/';
  const isMobile = useIsMobile();

  const onChange = (next: Locale) => {
    if (next === locale) return;
    setLocale(next);
    const target = localizedPath(next, stripLocale(pathname));
    router.push(target);
    router.refresh();
  };

  return (
    <label className="relative ml-1 inline-flex items-center">
      <span className="sr-only">{t('nav.language')}</span>
      <select
        aria-label={t('nav.language')}
        value={locale}
        onChange={(e) => onChange(e.target.value as Locale)}
        className="focus-ring appearance-none rounded-full border border-white/10 bg-transparent px-2 py-1.5 pr-6 text-xs uppercase tracking-[0.08em] text-muted hover:text-text sm:px-3 sm:pr-7"
      >
        {availableLocales.map((l) => (
          <option key={l} value={l} className="bg-surface text-text">
            {isMobile ? l.toUpperCase() : `${l.toUpperCase()} · ${localeLabels[l]}`}
          </option>
        ))}
      </select>
      <span
        aria-hidden
        className="pointer-events-none absolute right-1.5 text-2xs text-muted sm:right-2"
      >
        ▾
      </span>
    </label>
  );
}
