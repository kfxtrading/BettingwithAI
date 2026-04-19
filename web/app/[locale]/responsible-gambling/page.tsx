import type { Metadata } from 'next';
import { EditorialPage } from '@/components/EditorialPage';
import { buildMetadata } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-01';

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.responsibleGambling.title'],
    description: dict['page.responsibleGambling.description'],
    path: '/responsible-gambling',
    locale,
    ogType: 'article',
  });
}

type Helpline = { country: string; name: string; url: string; phone?: string };

const HELPLINES: Helpline[] = [
  {
    country: 'UK',
    name: 'GambleAware · National Gambling Helpline',
    url: 'https://www.gambleaware.org/',
    phone: '0808 8020 133',
  },
  {
    country: 'DE',
    name: 'BZgA · Check dein Spiel',
    url: 'https://www.check-dein-spiel.de/',
    phone: '0800 1 37 27 00',
  },
  {
    country: 'AT',
    name: 'Spielsuchthilfe Österreich',
    url: 'https://www.spielsuchthilfe.at/',
  },
  {
    country: 'CH',
    name: 'Sucht Schweiz · Spielsucht',
    url: 'https://www.suchtschweiz.ch/',
  },
  {
    country: 'FR',
    name: 'Joueurs Info Service',
    url: 'https://www.joueurs-info-service.fr/',
    phone: '09 74 75 13 13',
  },
  {
    country: 'IT',
    name: 'Telefono Verde Nazionale Dipendenze',
    url: 'https://www.iss.it/telefono-verde-droga-e-alcol',
    phone: '800 55 88 22',
  },
  {
    country: 'ES',
    name: 'FEJAR · Federación Española de Jugadores de Azar Rehabilitados',
    url: 'https://www.fejar.org/',
    phone: '900 200 225',
  },
];

const INTRO: Record<Locale, string> = {
  en: 'Gambling can be addictive. If you or someone close to you is struggling, free, confidential help is available in every country we serve. Take regular breaks, set a budget you can lose, never chase losses, and never bet to escape stress.',
  de: 'Glücksspiel kann süchtig machen. Wenn du oder jemand in deinem Umfeld Probleme hat, gibt es in jedem Land kostenlose und vertrauliche Hilfe. Mache regelmäßige Pausen, setze ein Budget, das du verlieren kannst, jage Verlusten nie hinterher und wette niemals, um Stress zu entfliehen.',
  fr: "Le jeu peut entraîner une dépendance. Si vous ou un proche êtes en difficulté, une aide gratuite et confidentielle est disponible dans chaque pays. Faites des pauses régulières, fixez un budget que vous pouvez perdre, ne courez jamais après les pertes et ne pariez jamais pour échapper au stress.",
  it: 'Il gioco può creare dipendenza. Se tu o una persona vicina avete difficoltà, in ogni paese è disponibile un aiuto gratuito e riservato. Fai pause regolari, fissa un budget che puoi perdere, non rincorrere mai le perdite e non scommettere mai per sfuggire allo stress.',
  es: 'El juego puede ser adictivo. Si tú o alguien cercano lo está pasando mal, en cada país hay ayuda gratuita y confidencial. Haz pausas regulares, fija un presupuesto que puedas perder, nunca persigas pérdidas y nunca apuestes para escapar del estrés.',
};

const TOOLS: Record<Locale, string> = {
  en: 'Self-exclusion tools: GAMSTOP (UK), OASIS (Germany), RUIJ (Spain), RNIE-FDJ (France), Registro Unico Autoesclusi (Italy).',
  de: 'Selbstsperr-Werkzeuge: OASIS (Deutschland), GAMSTOP (UK), RUIJ (Spanien), Registro Unico Autoesclusi (Italien), RNIE-FDJ (Frankreich).',
  fr: 'Outils d&apos;auto-exclusion : RNIE-FDJ et ANJ (France), GAMSTOP (UK), OASIS (Allemagne), RUIJ (Espagne), Registro Unico Autoesclusi (Italie).',
  it: 'Strumenti di autoesclusione: Registro Unico Autoesclusi (ADM, Italia), GAMSTOP (UK), OASIS (Germania), RUIJ (Spagna), RNIE-FDJ (Francia).',
  es: 'Herramientas de autoexclusión: RUIJ (España), GAMSTOP (Reino Unido), OASIS (Alemania), Registro Unico Autoesclusi (Italia), RNIE-FDJ (Francia).',
};

export default function ResponsibleGamblingPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.responsibleGambling.title']}
      description={dict['page.responsibleGambling.description']}
      path="/responsible-gambling"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        {
          name: dict['page.responsibleGambling.title'],
          path: '/responsible-gambling',
        },
      ]}
    >
      <p>{INTRO[locale]}</p>
      <h2>National helplines</h2>
      <ul>
        {HELPLINES.map((h) => (
          <li key={h.country}>
            <strong>{h.country}</strong> ·{' '}
            <a
              href={h.url}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="underline hover:text-text"
            >
              {h.name}
            </a>
            {h.phone ? <> · <span className="font-mono">{h.phone}</span></> : null}
          </li>
        ))}
      </ul>
      <h2>Self-exclusion</h2>
      <p>{TOOLS[locale]}</p>
    </EditorialPage>
  );
}
