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
    title: dict['page.terms.title'],
    description: dict['page.terms.description'],
    path: '/legal/terms',
    locale,
    ogType: 'article',
  });
}

const CONTENT: Record<Locale, () => JSX.Element> = {
  en: () => (
    <>
      <h2>1. Informational service</h2>
      <p>
        Betting with AI provides statistical analyses of football matches for
        informational and educational purposes only. We are not a bookmaker,
        we never accept stakes, and nothing on this site constitutes financial
        or betting advice.
      </p>
      <h2>2. No guarantees</h2>
      <p>
        Probabilities and value-bet flags are model output. They can and will
        be wrong. Past model performance is no guarantee of future results.
      </p>
      <h2>3. Eligibility</h2>
      <p>
        You must be at least 18 years old (or the legal gambling age in your
        jurisdiction, whichever is higher) to use this site for any
        gambling-related decision.
      </p>
      <h2>4. Liability</h2>
      <p>
        To the maximum extent permitted by law, Betting with AI accepts no
        liability for losses arising from any use of the information published
        on this site.
      </p>
      <h2>5. Governing law</h2>
      <p>
        These terms are governed by the laws of the Federal Republic of
        Germany. Place of jurisdiction is Berlin.
      </p>
    </>
  ),
  de: () => (
    <>
      <h2>1. Informationsangebot</h2>
      <p>
        Betting with AI stellt statistische Analysen von Fußballspielen
        ausschließlich zu Informations- und Bildungszwecken bereit. Wir sind
        kein Buchmacher, nehmen keine Einsätze entgegen und nichts auf dieser
        Website stellt eine Finanz- oder Wett-Beratung dar.
      </p>
      <h2>2. Keine Garantie</h2>
      <p>
        Wahrscheinlichkeiten und Value-Bet-Markierungen sind Modell-Output und
        können falsch liegen. Frühere Modell-Performance ist keine Garantie
        für zukünftige Ergebnisse.
      </p>
      <h2>3. Mindestalter</h2>
      <p>
        Du musst mindestens 18 Jahre alt sein (bzw. das gesetzliche Glücksspiel-
        Mindestalter deines Landes, je nachdem was höher ist), um diese
        Website für Glücksspiel-bezogene Entscheidungen zu nutzen.
      </p>
      <h2>4. Haftung</h2>
      <p>
        Im gesetzlich zulässigen Maximum übernimmt Betting with AI keine
        Haftung für Verluste, die aus der Nutzung der hier veröffentlichten
        Informationen entstehen.
      </p>
      <h2>5. Anwendbares Recht</h2>
      <p>
        Es gilt das Recht der Bundesrepublik Deutschland. Gerichtsstand ist
        Berlin.
      </p>
    </>
  ),
  fr: () => (
    <>
      <h2>1. Service informatif</h2>
      <p>
        Betting with AI fournit des analyses statistiques de matchs de
        football à des fins d&apos;information et d&apos;éducation
        uniquement. Nous ne sommes pas un bookmaker, nous n&apos;acceptons
        aucun enjeu, et rien sur ce site ne constitue un conseil financier ou
        de paris.
      </p>
      <h2>2. Aucune garantie</h2>
      <p>
        Les probabilités et value bets sont des sorties de modèle et peuvent
        être erronées. Les performances passées ne garantissent pas les
        résultats futurs.
      </p>
      <h2>3. Âge minimum</h2>
      <p>
        Vous devez avoir au moins 18 ans (ou l&apos;âge légal de jeu dans
        votre juridiction, selon le plus élevé) pour utiliser ce site dans le
        cadre de décisions de pari.
      </p>
      <h2>4. Responsabilité</h2>
      <p>
        Dans la mesure maximale autorisée par la loi, Betting with AI
        n&apos;accepte aucune responsabilité pour les pertes liées à
        l&apos;utilisation des informations publiées ici.
      </p>
      <h2>5. Droit applicable</h2>
      <p>
        Les présentes conditions sont régies par le droit de la République
        fédérale d&apos;Allemagne. Tribunal compétent : Berlin.
      </p>
    </>
  ),
  it: () => (
    <>
      <h2>1. Servizio informativo</h2>
      <p>
        Betting with AI fornisce analisi statistiche di partite di calcio a
        scopo esclusivamente informativo ed educativo. Non siamo un
        bookmaker, non accettiamo puntate e nulla in questo sito costituisce
        consulenza finanziaria o di scommessa.
      </p>
      <h2>2. Nessuna garanzia</h2>
      <p>
        Le probabilità e le value bet sono output di un modello e possono
        essere errate. Le performance passate non garantiscono risultati
        futuri.
      </p>
      <h2>3. Età minima</h2>
      <p>
        Devi avere almeno 18 anni (o l&apos;età legale per il gioco nella tua
        giurisdizione, quale più alta) per utilizzare questo sito a fini di
        decisioni di scommessa.
      </p>
      <h2>4. Responsabilità</h2>
      <p>
        Nella misura massima consentita dalla legge, Betting with AI non
        accetta alcuna responsabilità per perdite derivanti dall&apos;uso
        delle informazioni qui pubblicate.
      </p>
      <h2>5. Legge applicabile</h2>
      <p>
        Le presenti condizioni sono disciplinate dalle leggi della Repubblica
        Federale di Germania. Foro competente: Berlino.
      </p>
    </>
  ),
  es: () => (
    <>
      <h2>1. Servicio informativo</h2>
      <p>
        Betting with AI ofrece análisis estadísticos de partidos de fútbol con
        fines exclusivamente informativos y educativos. No somos una casa de
        apuestas, no aceptamos apuestas y nada en este sitio constituye
        asesoramiento financiero ni de apuestas.
      </p>
      <h2>2. Sin garantías</h2>
      <p>
        Las probabilidades y value bets son salida de un modelo y pueden ser
        incorrectas. El rendimiento pasado no garantiza resultados futuros.
      </p>
      <h2>3. Edad mínima</h2>
      <p>
        Debes tener al menos 18 años (o la edad legal para el juego en tu
        jurisdicción, la mayor) para utilizar este sitio con fines de
        decisiones de apuestas.
      </p>
      <h2>4. Responsabilidad</h2>
      <p>
        En la medida máxima permitida por la ley, Betting with AI no acepta
        responsabilidad alguna por pérdidas derivadas del uso de la
        información aquí publicada.
      </p>
      <h2>5. Ley aplicable</h2>
      <p>
        Estos términos se rigen por las leyes de la República Federal de
        Alemania. Jurisdicción: Berlín.
      </p>
    </>
  ),
};

export default function TermsPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const Body = CONTENT[locale];
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.terms.title']}
      description={dict['page.terms.description']}
      path="/legal/terms"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.terms.title'], path: '/legal/terms' },
      ]}
    >
      <Body />
    </EditorialPage>
  );
}
