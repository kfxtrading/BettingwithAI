import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { EducationalArticle } from '@/components/EducationalArticle';
import { buildMetadata } from '@/lib/seo';
import { getArticle, LEARN_SLUGS } from '@/content/learn';
import { locales, type Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale; slug: string } };

export function generateStaticParams(): { locale: Locale; slug: string }[] {
  const params: { locale: Locale; slug: string }[] = [];
  for (const locale of locales) {
    for (const slug of LEARN_SLUGS) {
      params.push({ locale, slug });
    }
  }
  return params;
}

export function generateMetadata({ params }: PageProps): Metadata {
  const article = getArticle(params.locale, params.slug);
  if (!article) {
    return { title: 'Not found', robots: { index: false, follow: false } };
  }
  return buildMetadata({
    title: article.title,
    description: article.description,
    path: `/learn/${article.slug}`,
    locale: params.locale,
    ogType: 'article',
  });
}

export default function LearnArticlePage({ params }: PageProps) {
  const article = getArticle(params.locale, params.slug);
  if (!article) {
    notFound();
  }
  return (
    <EducationalArticle
      locale={params.locale}
      article={article}
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: 'Learn', path: '/learn' },
        { name: article.title, path: `/learn/${article.slug}` },
      ]}
    />
  );
}
