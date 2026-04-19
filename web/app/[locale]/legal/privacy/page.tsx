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
    title: dict['page.privacy.title'],
    description: dict['page.privacy.description'],
    path: '/legal/privacy',
    locale,
    ogType: 'article',
  });
}

const CONTENT: Record<Locale, () => JSX.Element> = {
  en: () => (
    <>
      <h2>Controller</h2>
      <p>Betting with AI · contact: privacy@bettingwithai.app</p>
      <h2>Data we process</h2>
      <ul>
        <li>
          <strong>Server logs</strong> (IP-hash, user-agent, URL, timestamp) —
          stored 14 days for security and debugging. Lawful basis: Art. 6(1)(f)
          GDPR (legitimate interest).
        </li>
        <li>
          <strong>Cookie-consent record</strong> — your choice plus a hash of
          your IP, kept for one year. Lawful basis: Art. 6(1)(c) and (a) GDPR.
        </li>
        <li>
          <strong>Locale cookie</strong> (`NEXT_LOCALE`) — language preference,
          one year, strictly necessary.
        </li>
        <li>
          <strong>Analytics</strong> — only if you accept. Anonymised
          page-view counts, no cross-site tracking, no advertising.
        </li>
      </ul>
      <h2>Recipients</h2>
      <p>
        Hosting provider (Railway, USA — Standard Contractual Clauses).
        No data is sold or shared with bookmakers or affiliate networks.
      </p>
      <h2>Your rights</h2>
      <p>
        Access, rectification, erasure, restriction, portability, objection
        (Art. 15–21 GDPR), and the right to lodge a complaint with a
        supervisory authority. Email privacy@bettingwithai.app.
      </p>
      <h2>Retention</h2>
      <p>Logs: 14 days. Consent record: 12 months. Backups: 30 days.</p>
    </>
  ),
  de: () => (
    <>
      <h2>Verantwortlicher</h2>
      <p>Betting with AI · Kontakt: privacy@bettingwithai.app</p>
      <h2>Verarbeitete Daten</h2>
      <ul>
        <li>
          <strong>Server-Logs</strong> (IP-Hash, User-Agent, URL, Zeitstempel)
          — Speicherung 14 Tage zu Sicherheits- und Debugging-Zwecken.
          Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.
        </li>
        <li>
          <strong>Cookie-Einwilligungs-Datensatz</strong> — deine Wahl plus
          IP-Hash, ein Jahr aufbewahrt. Rechtsgrundlage: Art. 6 Abs. 1 lit. c
          und a DSGVO.
        </li>
        <li>
          <strong>Sprach-Cookie</strong> (`NEXT_LOCALE`) — Sprachpräferenz,
          ein Jahr, technisch notwendig.
        </li>
        <li>
          <strong>Analytics</strong> — nur bei Zustimmung. Anonymisierte
          Seitenaufrufe, kein Cross-Site-Tracking, keine Werbung.
        </li>
      </ul>
      <h2>Empfänger</h2>
      <p>
        Hosting-Provider (Railway, USA — Standardvertragsklauseln). Keine
        Weitergabe an Buchmacher oder Affiliate-Netzwerke.
      </p>
      <h2>Deine Rechte</h2>
      <p>
        Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit,
        Widerspruch (Art. 15–21 DSGVO) sowie Beschwerderecht bei einer
        Aufsichtsbehörde. E-Mail: privacy@bettingwithai.app.
      </p>
      <h2>Speicherdauer</h2>
      <p>Logs: 14 Tage. Einwilligungs-Datensatz: 12 Monate. Backups: 30 Tage.</p>
    </>
  ),
  fr: () => (
    <>
      <h2>Responsable du traitement</h2>
      <p>Betting with AI · contact : privacy@bettingwithai.app</p>
      <h2>Données traitées</h2>
      <ul>
        <li>
          <strong>Journaux serveur</strong> (hachage IP, user-agent, URL,
          horodatage) — conservés 14 jours pour la sécurité. Base légale :
          art. 6, §1, f) RGPD.
        </li>
        <li>
          <strong>Enregistrement de consentement</strong> — votre choix et un
          hachage de votre IP, conservés un an.
        </li>
        <li>
          <strong>Cookie de langue</strong> (`NEXT_LOCALE`) — préférence
          linguistique, un an, strictement nécessaire.
        </li>
        <li>
          <strong>Analytics</strong> — uniquement avec votre accord. Vues de
          pages anonymisées, pas de suivi inter-sites.
        </li>
      </ul>
      <h2>Destinataires</h2>
      <p>
        Hébergeur (Railway, USA — Clauses contractuelles types). Aucune
        donnée vendue à des bookmakers ou réseaux d&apos;affiliation.
      </p>
      <h2>Vos droits</h2>
      <p>
        Accès, rectification, effacement, limitation, portabilité, opposition
        (art. 15–21 RGPD) et droit de réclamation auprès de la CNIL. E-mail :
        privacy@bettingwithai.app.
      </p>
      <h2>Conservation</h2>
      <p>Journaux : 14 jours. Consentement : 12 mois. Sauvegardes : 30 jours.</p>
    </>
  ),
  it: () => (
    <>
      <h2>Titolare del trattamento</h2>
      <p>Betting with AI · contatto: privacy@bettingwithai.app</p>
      <h2>Dati trattati</h2>
      <ul>
        <li>
          <strong>Log del server</strong> (hash IP, user-agent, URL,
          timestamp) — conservati 14 giorni per sicurezza. Base giuridica:
          art. 6, par. 1, lett. f) GDPR.
        </li>
        <li>
          <strong>Registrazione del consenso</strong> — la tua scelta e un
          hash del tuo IP, conservati un anno.
        </li>
        <li>
          <strong>Cookie lingua</strong> (`NEXT_LOCALE`) — preferenza
          linguistica, un anno, strettamente necessario.
        </li>
        <li>
          <strong>Analytics</strong> — solo con il tuo consenso. Conteggi di
          pagine anonimi, nessun tracciamento cross-site.
        </li>
      </ul>
      <h2>Destinatari</h2>
      <p>
        Provider di hosting (Railway, USA — Clausole Contrattuali Standard).
        Nessun dato venduto a bookmaker o reti di affiliazione.
      </p>
      <h2>I tuoi diritti</h2>
      <p>
        Accesso, rettifica, cancellazione, limitazione, portabilità,
        opposizione (artt. 15–21 GDPR) e diritto di reclamo al Garante.
        Email: privacy@bettingwithai.app.
      </p>
      <h2>Conservazione</h2>
      <p>Log: 14 giorni. Consenso: 12 mesi. Backup: 30 giorni.</p>
    </>
  ),
  es: () => (
    <>
      <h2>Responsable del tratamiento</h2>
      <p>Betting with AI · contacto: privacy@bettingwithai.app</p>
      <h2>Datos tratados</h2>
      <ul>
        <li>
          <strong>Registros del servidor</strong> (hash de IP, user-agent,
          URL, marca temporal) — conservados 14 días por seguridad. Base
          legal: art. 6.1.f RGPD.
        </li>
        <li>
          <strong>Registro de consentimiento</strong> — tu elección y un hash
          de tu IP, conservados un año.
        </li>
        <li>
          <strong>Cookie de idioma</strong> (`NEXT_LOCALE`) — preferencia de
          idioma, un año, estrictamente necesaria.
        </li>
        <li>
          <strong>Analítica</strong> — solo con tu consentimiento. Recuentos
          de páginas anónimos, sin seguimiento entre sitios.
        </li>
      </ul>
      <h2>Destinatarios</h2>
      <p>
        Proveedor de hosting (Railway, EE. UU. — Cláusulas Contractuales
        Tipo). No se venden datos a casas de apuestas ni redes de
        afiliación.
      </p>
      <h2>Tus derechos</h2>
      <p>
        Acceso, rectificación, supresión, limitación, portabilidad y
        oposición (arts. 15–21 RGPD), y derecho a reclamar ante la AEPD.
        Email: privacy@bettingwithai.app.
      </p>
      <h2>Conservación</h2>
      <p>Logs: 14 días. Consentimiento: 12 meses. Backups: 30 días.</p>
    </>
  ),
};

export default function PrivacyPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const Body = CONTENT[locale];
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.privacy.title']}
      description={dict['page.privacy.description']}
      path="/legal/privacy"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.privacy.title'], path: '/legal/privacy' },
      ]}
    >
      <Body />
    </EditorialPage>
  );
}
