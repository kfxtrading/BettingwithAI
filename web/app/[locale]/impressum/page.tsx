import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { EditorialPage } from '@/components/EditorialPage';
import { buildMetadata } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-01';

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  if (locale !== 'de') {
    return {
      title: 'Impressum',
      robots: { index: false, follow: false },
    };
  }
  return buildMetadata({
    title: dict['page.impressum.title'],
    description: dict['page.impressum.description'],
    path: '/impressum',
    locale,
    ogType: 'article',
  });
}

export default function ImpressumPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  if (locale !== 'de') {
    notFound();
  }
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.impressum.title']}
      description={dict['page.impressum.description']}
      path="/impressum"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Startseite', path: '/' },
        { name: dict['page.impressum.title'], path: '/impressum' },
      ]}
    >
      <h2>Anbieter</h2>
      <p>
        Betting with AI
        <br />
        c/o Betreiber
        <br />
        Berlin, Deutschland
      </p>
      <h2>Kontakt</h2>
      <p>E-Mail: hello@bettingwithai.app</p>
      <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
      <p>Betreiber Betting with AI · Berlin</p>
      <h2>Haftungsausschluss</h2>
      <p>
        Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine Haftung
        für die Inhalte externer Links. Für den Inhalt der verlinkten Seiten
        sind ausschließlich deren Betreiber verantwortlich.
      </p>
      <h2>EU-Streitschlichtung</h2>
      <p>
        Die Europäische Kommission stellt eine Plattform zur
        Online-Streitbeilegung (OS) bereit:{' '}
        <a
          href="https://ec.europa.eu/consumers/odr/"
          rel="noopener noreferrer"
          target="_blank"
          className="underline"
        >
          https://ec.europa.eu/consumers/odr/
        </a>
        . Wir sind nicht bereit oder verpflichtet, an
        Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
        teilzunehmen.
      </p>
    </EditorialPage>
  );
}
