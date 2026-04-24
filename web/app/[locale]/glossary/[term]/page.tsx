import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { JsonLd } from '@/components/JsonLd';
import {
  absoluteUrl,
  buildMetadata,
  definedTermLd,
  localizedPath,
} from '@/lib/seo';
import {
  GLOSSARY_ENTRIES,
  GLOSSARY_SLUGS,
  getGlossaryEntry,
} from '@/content/glossary/en';
import { locales, type Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale; term: string } };

export function generateStaticParams(): { locale: Locale; term: string }[] {
  const params: { locale: Locale; term: string }[] = [];
  for (const locale of locales) {
    for (const slug of GLOSSARY_SLUGS) {
      params.push({ locale, term: slug });
    }
  }
  return params;
}

export function generateMetadata({ params }: PageProps): Metadata {
  const entry = getGlossaryEntry(params.term);
  if (!entry) {
    return { title: 'Not found', robots: { index: false, follow: false } };
  }
  return buildMetadata({
    title: `${entry.term} — definition`,
    description: entry.shortDefinition,
    path: `/glossary/${entry.slug}`,
    locale: params.locale,
    keywords: [entry.term, ...(entry.related ?? [])],
    ogType: 'article',
  });
}

export default function GlossaryTermPage({ params }: PageProps) {
  const entry = getGlossaryEntry(params.term);
  if (!entry) notFound();

  const locale = params.locale;
  const url = absoluteUrl(localizedPath(locale, `/glossary/${entry.slug}`));

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
      {
        '@type': 'ListItem',
        position: 3,
        name: entry.term,
        item: url,
      },
    ],
  };

  const termLd = definedTermLd({
    term: entry.term,
    description: entry.shortDefinition,
    url,
    termCode: entry.termCode,
    inDefinedTermSet: absoluteUrl(localizedPath(locale, '/glossary')),
  });

  const related = (entry.related ?? [])
    .map((slug) => GLOSSARY_ENTRIES.find((e) => e.slug === slug))
    .filter((e): e is (typeof GLOSSARY_ENTRIES)[number] => Boolean(e));

  return (
    <>
      <JsonLd data={[breadcrumbLd, termLd]} />
      <article className="prose-editorial mx-auto max-w-3xl">
        <header className="mb-6 border-b border-white/10 pb-6">
          <p className="text-2xs uppercase tracking-[0.08em] text-muted">
            Glossary
          </p>
          <h1 className="mt-2 text-3xl font-medium tracking-tight text-text">
            {entry.term}
            {entry.termCode && entry.termCode !== entry.term ? (
              <span className="ml-2 text-base font-normal text-muted">
                ({entry.termCode})
              </span>
            ) : null}
          </h1>
          <p className="mt-3 text-base text-muted">{entry.shortDefinition}</p>
          <p className="mt-4 text-2xs uppercase tracking-[0.08em] text-muted">
            Last updated{' '}
            <time dateTime={entry.lastUpdated}>{entry.lastUpdated}</time>
          </p>
        </header>

        <section className="text-sm leading-relaxed text-text">
          <p>{entry.body}</p>
        </section>

        {related.length > 0 ? (
          <section className="mt-10 border-t border-white/10 pt-6">
            <h2 className="text-sm font-medium uppercase tracking-[0.08em] text-muted">
              Related terms
            </h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {related.map((r) => (
                <li key={r.slug}>
                  <Link
                    href={localizedPath(locale, `/glossary/${r.slug}`)}
                    hrefLang={locale}
                    className="focus-ring inline-block rounded-md border border-white/10 bg-surface-1 px-3 py-1.5 text-sm text-text transition hover:bg-white/5"
                  >
                    {r.term}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </article>
    </>
  );
}
