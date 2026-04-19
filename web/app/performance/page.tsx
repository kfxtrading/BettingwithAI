import type { Metadata } from 'next';
import { PerformanceClient } from './PerformanceClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, absoluteUrl } from '@/lib/seo';

export const metadata: Metadata = buildMetadata({
  title: 'Model Performance · Hit Rate, ROI & Bankroll',
  description:
    'Full transparency over hit rate, ROI, maximum drawdown and per-league breakdowns of the Betting with AI ensemble model. Updated after every matchday.',
  path: '/performance',
});

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
