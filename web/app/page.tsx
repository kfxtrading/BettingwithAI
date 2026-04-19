import type { Metadata } from 'next';
import { HomeClient } from './HomeClient';
import { JsonLd } from '@/components/JsonLd';
import { buildMetadata, SITE_NAME, SITE_URL, absoluteUrl } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';

export function generateMetadata(): Metadata {
  const { locale, dict } = getServerDictionary();
  return buildMetadata({
    title: `${SITE_NAME} · ${dict['site.tagline']}`,
    description: dict['home.subheading'],
    path: '/',
    locale,
  });
}

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
