import type { Metadata } from 'next';
import { PerformanceClient } from './PerformanceClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, absoluteUrl } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';

export function generateMetadata(): Metadata {
  const { locale, dict } = getServerDictionary();
  return buildMetadata({
    title: dict['performance.heading'],
    description: dict['performance.description'],
    path: '/performance',
    locale,
  });
}

const breadcrumbLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Home', item: absoluteUrl('/') },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Performance',
      item: absoluteUrl('/performance'),
    },
  ],
};

export default function PerformancePage() {
  return (
    <>
      <JsonLd data={breadcrumbLd} />
      <PerformanceClient />
    </>
  );
}
