import type { ReactNode } from 'react';
import { JsonLd } from './JsonLd';
import { absoluteUrl, localizedPath, SITE_NAME } from '@/lib/seo';
import type { Locale } from '@/lib/i18n';

type Crumb = { name: string; path: string };

type EditorialPageProps = {
  locale: Locale;
  title: string;
  description: string;
  path: string;
  lastUpdated: string;
  breadcrumbs: Crumb[];
  /** Optional schema.org @type. Defaults to "Article". */
  schemaType?: 'Article' | 'AboutPage' | 'WebPage' | 'FAQPage';
  children: ReactNode;
};

export function EditorialPage({
  locale,
  title,
  description,
  path,
  lastUpdated,
  breadcrumbs,
  schemaType = 'Article',
  children,
}: EditorialPageProps) {
  const url = absoluteUrl(localizedPath(locale, path));

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      item: absoluteUrl(localizedPath(locale, c.path)),
    })),
  };

  const articleLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': schemaType,
    headline: title,
    description,
    url,
    inLanguage: locale,
    isPartOf: { '@type': 'WebSite', name: SITE_NAME, url: absoluteUrl('/') },
    dateModified: lastUpdated,
    author: { '@type': 'Organization', name: SITE_NAME },
    publisher: { '@type': 'Organization', name: SITE_NAME },
  };

  return (
    <>
      <JsonLd data={[breadcrumbLd, articleLd]} />
      <article className="prose-editorial mx-auto max-w-3xl">
        <header className="mb-8 border-b border-white/10 pb-6">
          <h1 className="text-3xl font-medium tracking-tight text-text">
            {title}
          </h1>
          <p className="mt-3 text-base text-muted">{description}</p>
          <dl className="mt-4 text-2xs uppercase tracking-[0.08em] text-muted">
            <dt className="sr-only">Last updated</dt>
            <dd>
              <time dateTime={lastUpdated}>Last updated · {lastUpdated}</time>
            </dd>
          </dl>
        </header>
        <div className="space-y-6 text-sm leading-relaxed text-text">
          {children}
        </div>
      </article>
    </>
  );
}
