import type { Metadata } from 'next';
import { PerformanceClient } from '@/app/performance/PerformanceClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, absoluteUrl, localizedPath } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';
import {
  fetchBankrollServer,
  fetchPerformanceSummaryServer,
} from '@/lib/server-api';

type PageProps = { params: { locale: Locale } };

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['performance.heading'],
    description: dict['performance.description'],
    path: '/performance',
    locale,
  });
}

export default async function PerformancePage({ params }: PageProps) {
  const [initialSummary, initialBankroll] = await Promise.all([
    fetchPerformanceSummaryServer(),
    fetchBankrollServer(),
  ]);

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: absoluteUrl(localizedPath(params.locale, '/')),
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Performance',
        item: absoluteUrl(localizedPath(params.locale, '/performance')),
      },
    ],
  };

  return (
    <>
      <JsonLd data={breadcrumbLd} />
      <PerformanceClient
        initialSummary={initialSummary}
        initialBankroll={initialBankroll}
      />
    </>
  );
}
