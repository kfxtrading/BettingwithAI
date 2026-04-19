import { JsonLd } from './JsonLd';
import { absoluteUrl, localizedPath, SITE_NAME } from '@/lib/seo';
import type { Locale } from '@/lib/i18n';
import type { LearnArticle } from '@/content/learn/types';

type EducationalArticleProps = {
  locale: Locale;
  article: LearnArticle;
  breadcrumbs: { name: string; path: string }[];
};

export function EducationalArticle({
  locale,
  article,
  breadcrumbs,
}: EducationalArticleProps) {
  const path = `/learn/${article.slug}`;
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

  const articleLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    url,
    inLanguage: locale,
    isPartOf: { '@type': 'WebSite', name: SITE_NAME, url: absoluteUrl('/') },
    dateModified: article.lastUpdated,
    ...(article.datePublished
      ? { datePublished: article.datePublished }
      : { datePublished: article.lastUpdated }),
    author: { '@type': 'Organization', name: SITE_NAME },
    publisher: { '@type': 'Organization', name: SITE_NAME },
    mainEntityOfPage: url,
  };

  const faqLd =
    article.faqs.length > 0
      ? {
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: article.faqs.map((f) => ({
            '@type': 'Question',
            name: f.question,
            acceptedAnswer: { '@type': 'Answer', text: f.answer },
          })),
        }
      : null;

  return (
    <>
      <JsonLd data={faqLd ? [breadcrumbLd, articleLd, faqLd] : [breadcrumbLd, articleLd]} />
      <article className="prose-editorial mx-auto max-w-3xl">
        <header className="mb-8 border-b border-white/10 pb-6">
          <h1 className="text-3xl font-medium tracking-tight text-text">
            {article.title}
          </h1>
          <p className="mt-3 text-base text-muted">{article.description}</p>
          <dl className="mt-4 text-2xs uppercase tracking-[0.08em] text-muted">
            <dt className="sr-only">Last updated</dt>
            <dd>
              <time dateTime={article.lastUpdated}>
                Last updated · {article.lastUpdated}
              </time>
            </dd>
          </dl>
        </header>

        <div className="space-y-6 text-sm leading-relaxed text-text">
          <aside className="rounded-md border border-white/10 bg-white/5 p-4">
            <p className="m-0 text-2xs uppercase tracking-[0.08em] text-muted">
              TL;DR
            </p>
            <p className="mt-2 m-0">{article.tldr}</p>
          </aside>

          {article.sections.map((section) => (
            <section key={section.heading}>
              <h2>{section.heading}</h2>
              {section.paragraphs.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </section>
          ))}

          {article.faqs.length > 0 && (
            <section>
              <h2>Frequently asked questions</h2>
              <dl className="space-y-4">
                {article.faqs.map((f) => (
                  <div key={f.question}>
                    <dt className="font-medium text-text">{f.question}</dt>
                    <dd className="mt-1 text-muted">{f.answer}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </div>
      </article>
    </>
  );
}
