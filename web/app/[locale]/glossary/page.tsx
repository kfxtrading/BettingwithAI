import type { Metadata } from 'next';
import Link from 'next/link';
import { JsonLd } from '@/components/JsonLd';
import {
  absoluteUrl,
  buildMetadata,
  localizedPath,
  SITE_NAME,
} from '@/lib/seo';
import { GLOSSARY_ENTRIES } from '@/content/glossary/en';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const TITLE = 'Betting & AI Glossary — key terms explained';
const DESCRIPTION =
  'Concise definitions of the core terms used across Betting with AI: value bet, expected value, Kelly criterion, pi-rating, CatBoost, calibration, CLV and more.';

export function generateMetadata({ params }: PageProps): Metadata {
  return buildMetadata({
    title: TITLE,
    description: DESCRIPTION,
    path: '/glossary',
    locale: params.locale,
    keywords: GLOSSARY_ENTRIES.map((e) => e.term),
  });
}

export default function GlossaryIndexPage({ params }: PageProps) {
  const locale = params.locale;

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: absoluteUrl(localizedPath(locale, '/')),
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Glossary',
        item: absoluteUrl(localizedPath(locale, '/glossary')),
      },
    ],
  };

  const definedTermSetLd = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTermSet',
    name: `${SITE_NAME} Glossary`,
    url: absoluteUrl(localizedPath(locale, '/glossary')),
    hasDefinedTerm: GLOSSARY_ENTRIES.map((e) => ({
      '@type': 'DefinedTerm',
      name: e.term,
      description: e.shortDefinition,
      url: absoluteUrl(localizedPath(locale, `/glossary/${e.slug}`)),
      ...(e.termCode ? { termCode: e.termCode } : {}),
    })),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, definedTermSetLd]} />
      <section className="mx-auto max-w-3xl">
        <header className="mb-10 border-b border-white/10 pb-6">
          <p className="text-2xs uppercase tracking-[0.08em] text-muted">
            Glossary
          </p>
          <h1 className="mt-2 text-3xl font-medium tracking-tight text-text">
            Betting &amp; AI glossary
          </h1>
          <p className="mt-3 text-base text-muted">{DESCRIPTION}</p>
        </header>

        <ul className="grid gap-4 sm:grid-cols-2">
          {GLOSSARY_ENTRIES.map((e) => (
            <li key={e.slug}>
              <Link
                href={localizedPath(locale, `/glossary/${e.slug}`)}
                hrefLang={locale}
                className="surface-card focus-ring block h-full px-5 py-4 transition hover:bg-white/5"
              >
                <h2 className="text-base font-medium text-text">{e.term}</h2>
                <p className="mt-2 text-sm text-muted">{e.shortDefinition}</p>
                <p className="mt-3 text-2xs uppercase tracking-[0.08em] text-accent">
                  Read definition
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
