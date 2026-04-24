import type { Metadata } from 'next';
import { HomeClient } from '@/app/HomeClient';
import { JsonLd } from '@/components/JsonLd';
import { FaqSection } from '@/components/FaqSection';
import { HOME_FAQ, HOME_FAQ_LAST_UPDATED } from '@/content/home-faq';
import {
  buildMetadata,
  SITE_NAME,
  SITE_URL,
  absoluteUrl,
  localizedPath,
} from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';
import { fetchLeaguesServer, fetchTodayServer } from '@/lib/server-api';

type PageProps = { params: { locale: Locale } };

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
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

export default async function HomePage({ params }: PageProps) {
  const [initialToday, initialLeagues] = await Promise.all([
    fetchTodayServer(),
    fetchLeaguesServer(),
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
    ],
  };

  return (
    <>
      <JsonLd data={[sportsOrgLd, breadcrumbLd]} />
      <HomeClient
        initialToday={initialToday}
        initialLeagues={initialLeagues}
      />
      <FaqSection
        heading="Frequently asked questions"
        intro="Concise answers to the questions we get most often about the model, the data and how to use the value bets."
        items={HOME_FAQ}
        lastUpdated={HOME_FAQ_LAST_UPDATED}
      />
    </>
  );
}
