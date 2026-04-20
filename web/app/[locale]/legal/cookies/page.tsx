import type { Metadata } from 'next';
import { EditorialPage } from '@/components/EditorialPage';
import { buildMetadata } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-20';

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.cookies.title'],
    description: dict['page.cookies.description'],
    path: '/legal/cookies',
    locale,
    ogType: 'article',
  });
}

type Row = { name: string; purpose: string; duration: string; type: string };

const ROWS: Row[] = [
  {
    name: 'NEXT_LOCALE',
    purpose: 'Stores your selected language to keep the site in your locale.',
    duration: '12 months',
    type: 'Necessary',
  },
  {
    name: 'cookie_consent',
    purpose: 'Records your cookie-banner choice (necessary / analytics / marketing).',
    duration: '12 months',
    type: 'Necessary',
  },
  {
    name: '_anon_pageview',
    purpose: 'Anonymous page-view counter — only set if you accept analytics.',
    duration: 'Session',
    type: 'Analytics (opt-in)',
  },
  {
    name: 'Sofascore widget',
    purpose:
      'Loads live lineups and player ratings on match pages. The iframe may set its own cookies and receive your IP address, browser metadata and referrer.',
    duration: 'Set by provider',
    type: 'Third-party widget',
  },
];

const INTRO: Record<Locale, string> = {
  en: 'We use a small number of first-party cookies to operate the site and, only with your consent, to measure aggregate usage. Match pages can also load a Sofascore iframe that may set third-party cookies when the widget is displayed.',
  de: 'Wir verwenden eine kleine Anzahl eigener Cookies, um die Seite zu betreiben und — nur mit deiner Einwilligung — die Nutzung zu messen. Auf Match-Seiten kann zusätzlich ein Sofascore-iframe geladen werden, das beim Anzeigen des Widgets Drittanbieter-Cookies setzen kann.',
  fr: "Nous utilisons un petit nombre de cookies propriétaires pour faire fonctionner le site et, uniquement avec votre consentement, mesurer l'usage agrégé. Les pages de match peuvent aussi charger une iframe Sofascore susceptible de déposer des cookies tiers lors de l'affichage du widget.",
  it: 'Utilizziamo un piccolo numero di cookie proprietari per far funzionare il sito e, solo con il tuo consenso, per misurare l\'uso aggregato. Le pagine partita possono inoltre caricare un iframe Sofascore che può impostare cookie di terze parti quando il widget viene mostrato.',
  es: 'Utilizamos un pequeño número de cookies propias para operar el sitio y, solo con tu consentimiento, para medir el uso agregado. Las páginas de partido también pueden cargar un iframe de Sofascore que puede establecer cookies de terceros cuando se muestra el widget.',
};

const COL: Record<Locale, [string, string, string, string]> = {
  en: ['Name', 'Purpose', 'Duration', 'Category'],
  de: ['Name', 'Zweck', 'Dauer', 'Kategorie'],
  fr: ['Nom', 'Objectif', 'Durée', 'Catégorie'],
  it: ['Nome', 'Finalità', 'Durata', 'Categoria'],
  es: ['Nombre', 'Finalidad', 'Duración', 'Categoría'],
};

export default function CookiesPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const cols = COL[locale];
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.cookies.title']}
      description={dict['page.cookies.description']}
      path="/legal/cookies"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.cookies.title'], path: '/legal/cookies' },
      ]}
    >
      <p>{INTRO[locale]}</p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b border-white/10 text-left text-2xs uppercase tracking-[0.08em] text-muted">
              <th className="py-2 pr-4">{cols[0]}</th>
              <th className="py-2 pr-4">{cols[1]}</th>
              <th className="py-2 pr-4">{cols[2]}</th>
              <th className="py-2 pr-4">{cols[3]}</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.name} className="border-b border-white/5">
                <td className="py-2 pr-4 font-mono">{r.name}</td>
                <td className="py-2 pr-4">{r.purpose}</td>
                <td className="py-2 pr-4">{r.duration}</td>
                <td className="py-2 pr-4">{r.type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </EditorialPage>
  );
}
