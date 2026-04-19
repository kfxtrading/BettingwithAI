import type { Metadata } from 'next';
import { HomeClient } from './HomeClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, SITE_NAME, SITE_URL, absoluteUrl } from '@/lib/seo';

export const metadata: Metadata = buildMetadata({
  title: `${SITE_NAME} · AI-driven football predictions & value bets`,
  description:
    "Today's AI-driven football betting analyses for the Top 5 leagues. Calibrated probabilities for Home, Draw, Away — plus value bets where the model disagrees with the market.",
  path: '/',
});

const sportsOrgLd = {
  '@context': 'https://schema.org',
  '@type': 'SportsOrganization',
  name: SITE_NAME,
  url: SITE_URL,
  sport: 'Association football',
};

const breadcrumbLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Home',
      item: absoluteUrl('/'),
    },
  ],
};

export default function HomePage() {
  return (
    <>
      <JsonLd data={[sportsOrgLd, breadcrumbLd]} />
      <HomeClient />
    </>
  );
}
