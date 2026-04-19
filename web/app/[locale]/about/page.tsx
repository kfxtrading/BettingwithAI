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
    title: dict['page.about.title'],
    description: dict['page.about.description'],
    path: '/about',
    locale,
    ogType: 'article',
  });
}

const CONTENT: Record<Locale, () => JSX.Element> = {
  en: () => (
    <>
      <h2>Why Betting with AI exists</h2>
      <p>
        Most football prediction sites are powered by bookmaker affiliate
        revenue. They earn when you lose. <strong>Betting with AI</strong> is
        different: we ship no affiliate links, accept no sponsored content and
        publish our model performance, including losses, in full.
      </p>
      <h2>Who builds it</h2>
      <p>
        A solo data scientist with a background in statistical modelling and
        machine learning. The full source code, methodology and changelog are
        public.
      </p>
      <h2>What you get</h2>
      <ul>
        <li>Calibrated 1X2 probabilities for the Top 5 European leagues.</li>
        <li>Value-bet detection using market-removed implied probabilities.</li>
        <li>A live, public accuracy and ROI tracker — wins and losses.</li>
        <li>Plain-language methodology pages, never marketing copy.</li>
      </ul>
    </>
  ),
  de: () => (
    <>
      <h2>Warum es Betting with AI gibt</h2>
      <p>
        Die meisten Tipp-Seiten leben von Affiliate-Provisionen der Buchmacher
        und verdienen, wenn du verlierst. <strong>Betting with AI</strong>{' '}
        macht es anders: keine Affiliate-Links, keine bezahlten Inhalte und
        eine vollständig öffentliche Modell-Performance — inklusive Verluste.
      </p>
      <h2>Wer dahintersteht</h2>
      <p>
        Ein einzelner Data Scientist mit Hintergrund in statistischer
        Modellierung und Machine Learning. Quellcode, Methodik und Changelog
        sind öffentlich.
      </p>
      <h2>Was du bekommst</h2>
      <ul>
        <li>Kalibrierte 1X2-Wahrscheinlichkeiten für die Top-5-Ligen.</li>
        <li>Value-Bet-Erkennung mit margenbereinigten Quoten.</li>
        <li>Öffentlicher Accuracy- und ROI-Tracker — Gewinne und Verluste.</li>
        <li>Verständliche Methodik-Seiten, kein Marketing-Sprech.</li>
      </ul>
    </>
  ),
  fr: () => (
    <>
      <h2>Pourquoi Betting with AI existe</h2>
      <p>
        La plupart des sites de pronostics vivent des commissions des
        bookmakers et gagnent quand vous perdez.{' '}
        <strong>Betting with AI</strong> fonctionne autrement : aucun lien
        affilié, aucun contenu sponsorisé et des performances de modèle
        entièrement publiques, pertes comprises.
      </p>
      <h2>Qui le construit</h2>
      <p>
        Un data scientist solo avec un parcours en modélisation statistique et
        machine learning. Code source, méthodologie et changelog sont publics.
      </p>
      <h2>Ce que vous obtenez</h2>
      <ul>
        <li>Probabilités 1N2 calibrées pour les cinq grands championnats.</li>
        <li>Détection de value bets via cotes nettes de marge.</li>
        <li>Suivi public de précision et ROI — gains et pertes.</li>
        <li>Pages méthodologiques claires, sans discours marketing.</li>
      </ul>
    </>
  ),
  it: () => (
    <>
      <h2>Perché esiste Betting with AI</h2>
      <p>
        La maggior parte dei siti di pronostici vive di commissioni di
        affiliazione dei bookmaker e guadagna quando perdi tu.{' '}
        <strong>Betting with AI</strong> è diverso: nessun link affiliato,
        nessun contenuto sponsorizzato e performance del modello completamente
        pubbliche, perdite incluse.
      </p>
      <h2>Chi lo costruisce</h2>
      <p>
        Un singolo data scientist con esperienza in modelli statistici e
        machine learning. Codice sorgente, metodologia e changelog sono
        pubblici.
      </p>
      <h2>Cosa ottieni</h2>
      <ul>
        <li>Probabilità 1X2 calibrate per i top 5 campionati europei.</li>
        <li>Rilevazione di value bet con quote nette di margine.</li>
        <li>Tracker pubblico di precisione e ROI — vittorie e perdite.</li>
        <li>Pagine di metodologia chiare, niente linguaggio di marketing.</li>
      </ul>
    </>
  ),
  es: () => (
    <>
      <h2>Por qué existe Betting with AI</h2>
      <p>
        La mayoría de sitios de pronósticos vive de comisiones de afiliación
        de las casas de apuestas y gana cuando tú pierdes.{' '}
        <strong>Betting with AI</strong> es distinto: sin enlaces de
        afiliación, sin contenido patrocinado y con el rendimiento del modelo
        totalmente público, pérdidas incluidas.
      </p>
      <h2>Quién lo construye</h2>
      <p>
        Un científico de datos en solitario con experiencia en modelado
        estadístico y machine learning. Código fuente, metodología y changelog
        son públicos.
      </p>
      <h2>Qué obtienes</h2>
      <ul>
        <li>Probabilidades 1X2 calibradas para las cinco grandes ligas.</li>
        <li>Detección de value bets con cuotas netas de margen.</li>
        <li>Tracker público de precisión y ROI — ganancias y pérdidas.</li>
        <li>Páginas de metodología claras, sin lenguaje de marketing.</li>
      </ul>
    </>
  ),
};

export default function AboutPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const Body = CONTENT[locale];
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.about.title']}
      description={dict['page.about.description']}
      path="/about"
      lastUpdated={LAST_UPDATED}
      schemaType="AboutPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.about.title'], path: '/about' },
      ]}
    >
      <Body />
    </EditorialPage>
  );
}
