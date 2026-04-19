'use client';

import { useRouter } from 'next/navigation';
import { useLocale } from '@/lib/i18n/LocaleProvider';
import { localeLabels, type Locale } from '@/lib/i18n';

export function LanguageSwitcher() {
  const { locale, setLocale, availableLocales, t } = useLocale();
  const router = useRouter();

  const onChange = (next: Locale) => {
    if (next === locale) return;
    setLocale(next);
    router.refresh();
  };

  return (
    <label className="relative ml-1 inline-flex items-center">
      <span className="sr-only">{t('nav.language')}</span>
      <select
        aria-label={t('nav.language')}
        value={locale}
        onChange={(e) => onChange(e.target.value as Locale)}
        className="focus-ring appearance-none rounded-full border border-white/10 bg-transparent px-3 py-1.5 pr-7 text-xs uppercase tracking-[0.08em] text-muted hover:text-text"
      >
        {availableLocales.map((l) => (
          <option key={l} value={l} className="bg-surface text-text">
            {l.toUpperCase()} · {localeLabels[l]}
          </option>
        ))}
      </select>
      <span
        aria-hidden
        className="pointer-events-none absolute right-2 text-2xs text-muted"
      >
        ▾
      </span>
    </label>
  );
}
