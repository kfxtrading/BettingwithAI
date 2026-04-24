import type { Metadata } from 'next';
import Link from 'next/link';
import { JsonLd } from '@/components/JsonLd';
import { absoluteUrl, buildMetadata, localizedPath, SITE_NAME } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import { listArticles } from '@/content/learn';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.learn.title'],
    description: dict['page.learn.description'],
    path: '/learn',
    locale,
  });
}

export default function LearnHubPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const articles = listArticles(locale);

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
        name: 'Learn',
        item: absoluteUrl(localizedPath(locale, '/learn')),
      },
    ],
  };

  const itemListLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `${SITE_NAME} · Learn`,
    itemListElement: articles.map((a, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: absoluteUrl(localizedPath(locale, `/learn/${a.slug}`)),
      name: a.title,
    })),
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, itemListLd]} />
      <section className="mx-auto max-w-3xl">
        <header className="mb-10 border-b border-white/10 pb-6">
          <p className="text-2xs uppercase tracking-[0.08em] text-muted">
            {dict['rail.quick.learn']}
          </p>
          <h1 className="mt-2 text-3xl font-medium tracking-tight text-text">
            {dict['learn.heading']}
          </h1>
          <p className="mt-3 text-base text-muted">{dict['learn.intro']}</p>
        </header>

        <ul className="grid gap-4 sm:grid-cols-2">
          {articles.map((a) => (
            <li key={a.slug}>
              <Link
                href={localizedPath(locale, `/learn/${a.slug}`)}
                hrefLang={locale}
                className="surface-card focus-ring block h-full px-5 py-4 transition hover:bg-white/5"
              >
                <h2 className="text-base font-medium text-text">{a.title}</h2>
                <p className="mt-2 text-sm text-muted">{a.description}</p>
                <p className="mt-3 text-2xs uppercase tracking-[0.08em] text-accent">
                  {dict['learn.readMore']}
                </p>
              </Link>
            </li>
          ))}
        </ul>

        <aside className="mt-10 border-t border-white/10 pt-6">
          <p className="text-sm text-muted">
            Looking for a quick definition instead of a long read?{' '}
            <Link
              href={localizedPath(locale, '/glossary')}
              hrefLang={locale}
              className="text-accent underline-offset-4 hover:underline"
            >
              Browse the glossary
            </Link>{' '}
            for concise, citable explanations of every key term.
          </p>
        </aside>
      </section>
    </>
  );
}
