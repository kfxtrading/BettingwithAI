'use client';

import Link from 'next/link';
import { useLocale } from '@/lib/i18n/LocaleProvider';

type FooterLink = {
  href: string;
  labelKey:
    | 'footer.link.today'
    | 'footer.link.leagues'
    | 'footer.link.performance'
    | 'footer.link.terms'
    | 'footer.link.privacy'
    | 'footer.link.cookies'
    | 'footer.link.impressum'
    | 'footer.link.responsibleGambling'
    | 'footer.link.helpline'
    | 'footer.link.investors';
  external?: boolean;
  onlyLocale?: string;
};

const PRODUCT_LINKS: FooterLink[] = [
  { href: '/', labelKey: 'footer.link.today' },
  { href: '/leagues', labelKey: 'footer.link.leagues' },
  { href: '/performance', labelKey: 'footer.link.performance' },
];

const COMPANY_LINKS: FooterLink[] = [
  { href: '/investors', labelKey: 'footer.link.investors' },
];

const LEGAL_LINKS: FooterLink[] = [
  { href: '/legal/terms', labelKey: 'footer.link.terms' },
  { href: '/legal/privacy', labelKey: 'footer.link.privacy' },
  { href: '/legal/cookies', labelKey: 'footer.link.cookies' },
  { href: '/impressum', labelKey: 'footer.link.impressum', onlyLocale: 'de' },
];

const HELPLINE_BY_LOCALE: Record<string, { url: string }> = {
  en: { url: 'https://www.gambleaware.org/' },
  de: { url: 'https://www.check-dein-spiel.de/' },
  fr: { url: 'https://www.joueurs-info-service.fr/' },
  it: { url: 'https://www.iss.it/telefono-verde-droga-e-alcol' },
  es: { url: 'https://www.fejar.org/' },
};

export function Footer() {
  const { t, locale, href } = useLocale();
  const helpline = HELPLINE_BY_LOCALE[locale] ?? HELPLINE_BY_LOCALE.en;
  const responsibleLinks: FooterLink[] = [
    {
      href: '/responsible-gambling',
      labelKey: 'footer.link.responsibleGambling',
    },
  ];

  const renderLink = (link: FooterLink) => {
    if (link.onlyLocale && link.onlyLocale !== locale) return null;
    const label = t(link.labelKey);
    if (link.external) {
      return (
        <li key={link.href}>
          <a
            href={link.href}
            rel="noopener noreferrer nofollow"
            target="_blank"
            className="focus-ring rounded-sm hover:text-text"
          >
            {label}
          </a>
        </li>
      );
    }
    return (
      <li key={link.href}>
        <Link
          href={href(link.href)}
          hrefLang={locale}
          className="focus-ring rounded-sm hover:text-text"
        >
          {label}
        </Link>
      </li>
    );
  };

  return (
    <footer className="mx-auto w-full max-w-page px-6 pb-12 pt-10 text-2xs text-muted md:px-12">
      <div className="hairline pt-8">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.08em] text-text">
              {t('footer.col.product')}
            </h2>
            <ul className="flex flex-col gap-2">{PRODUCT_LINKS.map(renderLink)}</ul>
          </div>
          <div>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.08em] text-text">
              {t('footer.col.company')}
            </h2>
            <ul className="flex flex-col gap-2">{COMPANY_LINKS.map(renderLink)}</ul>
          </div>
          <div>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.08em] text-text">
              {t('footer.col.legal')}
            </h2>
            <ul className="flex flex-col gap-2">{LEGAL_LINKS.map(renderLink)}</ul>
          </div>
          <div>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.08em] text-text">
              {t('footer.col.responsible')}
            </h2>
            <ul className="flex flex-col gap-2">
              {responsibleLinks.map(renderLink)}
              <li>
                <a
                  href={helpline.url}
                  rel="noopener noreferrer nofollow"
                  target="_blank"
                  className="focus-ring rounded-sm hover:text-text"
                >
                  {t('footer.link.helpline')} ↗
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-3 border-t border-white/5 pt-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <span
              aria-label={t('footer.ageBadge.label')}
              className="inline-flex items-center gap-1 rounded-full border border-white/15 px-2 py-0.5 text-2xs font-medium text-text"
            >
              <span className="font-mono">18+</span>
              <span className="text-muted">·</span>
              <span className="text-muted">{t('footer.ageBadge.label')}</span>
            </span>
            <span>{t('footer.text')}</span>
          </div>
        </div>

        <p className="mt-4 max-w-3xl text-2xs leading-relaxed text-muted">
          {t('footer.disclaimer')}
        </p>
      </div>
    </footer>
  );
}
