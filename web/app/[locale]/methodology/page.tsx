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
    title: dict['page.methodology.title'],
    description: dict['page.methodology.description'],
    path: '/methodology',
    locale,
    ogType: 'article',
  });
}

const CONTENT: Record<Locale, () => JSX.Element> = {
  en: () => (
    <>
      <h2>The ensemble in 60 seconds</h2>
      <p>
        Each match is scored by three independent models — a Dixon-Coles Poisson
        goal model, a CatBoost gradient-boosted classifier and a PyTorch MLP —
        whose probabilities are blended by a Dirichlet-tuned weighted average,
        then post-calibrated with isotonic regression. Final probabilities are
        compared to market-removed bookmaker odds; positive expected-value bets
        are surfaced and sized via fractional Kelly.
      </p>
      <h2>Pi-Ratings (input)</h2>
      <p>
        We start from Constantinou &amp; Fenton&apos;s Pi-Ratings (2013), with
        separate home and away strength components. Pi-Ratings update after
        every match using a learning rate tuned per league.
      </p>
      <h2>Feature engineering</h2>
      <p>
        70+ features per match: rating differentials, recent form, expected
        goals (xG) where available, head-to-head priors, rest days, market
        consensus probability, league-specific home advantage and more.
      </p>
      <h2>Calibration &amp; honesty</h2>
      <p>
        We track Brier score, Ranked Probability Score (RPS) and Expected
        Calibration Error (ECE). The target is ECE &lt; 1.5% after isotonic
        post-calibration. Performance is reported per league and over time on
        the public tracker.
      </p>
      <h2>Limitations</h2>
      <p>
        No model is perfect. Edges shrink as bookmakers update, injury
        information leaks to markets faster than to public sources, and
        weather/lineup uncertainty is hard to capture. Past performance never
        guarantees future returns.
      </p>
      <h2>Retraining cadence</h2>
      <p>
        Walk-forward retraining after every matchday for Pi-Ratings; full model
        re-fit weekly. Drift is monitored via KS-test against rolling
        baselines.
      </p>
    </>
  ),
  de: () => (
    <>
      <h2>Das Ensemble in 60 Sekunden</h2>
      <p>
        Jedes Spiel wird von drei unabhängigen Modellen bewertet — einem
        Dixon-Coles-Poisson-Tor-Modell, einem CatBoost-Gradient-Boosting-
        Klassifikator und einem PyTorch-MLP. Die Wahrscheinlichkeiten werden
        per Dirichlet-getunter gewichteter Mittelung kombiniert und mit
        isotonischer Regression nachkalibriert. Die finalen Wahrscheinlichkeiten
        werden mit margenbereinigten Buchmacherquoten verglichen; positive
        Value Bets werden mit Fractional-Kelly dimensioniert.
      </p>
      <h2>Pi-Ratings (Input)</h2>
      <p>
        Basis sind die Pi-Ratings nach Constantinou &amp; Fenton (2013) mit
        getrennten Heim- und Auswärtskomponenten. Pi-Ratings werden nach jedem
        Spiel mit einer ligaspezifisch optimierten Lernrate aktualisiert.
      </p>
      <h2>Feature Engineering</h2>
      <p>
        70+ Features pro Spiel: Rating-Differenzen, jüngste Form, Expected
        Goals (xG) wo verfügbar, Direktvergleichs-Priors, Ruhetage,
        Marktkonsens, ligaspezifischer Heimvorteil und mehr.
      </p>
      <h2>Kalibrierung &amp; Ehrlichkeit</h2>
      <p>
        Wir tracken Brier-Score, Ranked Probability Score (RPS) und Expected
        Calibration Error (ECE). Ziel ist ECE &lt; 1,5 % nach isotonischer
        Nachkalibrierung. Die Performance wird pro Liga und über die Zeit im
        öffentlichen Tracker ausgewiesen.
      </p>
      <h2>Grenzen</h2>
      <p>
        Kein Modell ist perfekt. Edges verschwinden, sobald Buchmacher
        nachziehen; Verletzungs-Information erreicht Märkte schneller als
        öffentliche Quellen; Wetter und Aufstellungs-Unsicherheit sind schwer
        abbildbar. Frühere Ergebnisse garantieren keine zukünftigen.
      </p>
      <h2>Retraining-Rhythmus</h2>
      <p>
        Walk-Forward-Retraining der Pi-Ratings nach jedem Spieltag, komplettes
        Modell-Refit wöchentlich. Drift wird per KS-Test gegen rollende
        Baselines überwacht.
      </p>
    </>
  ),
  fr: () => (
    <>
      <h2>L&apos;ensemble en 60 secondes</h2>
      <p>
        Chaque match est noté par trois modèles indépendants — un modèle
        Poisson Dixon-Coles, un classifieur CatBoost et un MLP PyTorch — dont
        les probabilités sont combinées par moyenne pondérée Dirichlet, puis
        post-calibrées avec une régression isotonique. Les probabilités finales
        sont comparées aux cotes nettes de marge ; les value bets à valeur
        attendue positive sont affichées et dimensionnées via Kelly
        fractionnel.
      </p>
      <h2>Pi-Ratings (entrée)</h2>
      <p>
        Nous partons des Pi-Ratings de Constantinou &amp; Fenton (2013), avec
        des composantes domicile et extérieur séparées, mises à jour après
        chaque match.
      </p>
      <h2>Feature engineering</h2>
      <p>
        Plus de 70 caractéristiques par match : différentiels de rating, forme
        récente, expected goals (xG) si disponibles, priors face-à-face, jours
        de repos, consensus de marché, avantage du terrain par championnat,
        etc.
      </p>
      <h2>Calibration &amp; honnêteté</h2>
      <p>
        Nous suivons le score de Brier, le Ranked Probability Score (RPS) et
        l&apos;Expected Calibration Error (ECE). Cible : ECE &lt; 1,5 % après
        post-calibration isotonique. Performance publiée par championnat et
        dans le temps.
      </p>
      <h2>Limites</h2>
      <p>
        Aucun modèle n&apos;est parfait. Les edges fondent quand les
        bookmakers ajustent ; l&apos;information sur les blessures atteint le
        marché plus vite que les sources publiques. Les performances passées
        ne garantissent rien.
      </p>
      <h2>Cadence de réentraînement</h2>
      <p>
        Réentraînement walk-forward des Pi-Ratings après chaque journée ;
        refit complet du modèle chaque semaine. Drift surveillé par test KS.
      </p>
    </>
  ),
  it: () => (
    <>
      <h2>L&apos;ensemble in 60 secondi</h2>
      <p>
        Ogni partita viene valutata da tre modelli indipendenti — un modello
        Poisson Dixon-Coles, un classificatore CatBoost e un MLP PyTorch — le
        cui probabilità vengono combinate con una media pesata ottimizzata
        Dirichlet, poi post-calibrate con regressione isotonica. Le
        probabilità finali vengono confrontate con quote nette di margine; le
        value bet a valore atteso positivo vengono evidenziate e dimensionate
        con Kelly frazionario.
      </p>
      <h2>Pi-Ratings (input)</h2>
      <p>
        Partiamo dai Pi-Ratings di Constantinou &amp; Fenton (2013), con
        componenti separate per casa e trasferta, aggiornati dopo ogni
        partita.
      </p>
      <h2>Feature engineering</h2>
      <p>
        Oltre 70 feature per partita: differenziali di rating, forma recente,
        expected goals (xG) ove disponibili, prior negli scontri diretti,
        giorni di riposo, consenso di mercato, vantaggio casalingo per
        campionato e altro.
      </p>
      <h2>Calibrazione &amp; onestà</h2>
      <p>
        Tracciamo Brier score, Ranked Probability Score (RPS) ed Expected
        Calibration Error (ECE). Obiettivo: ECE &lt; 1,5% dopo
        post-calibrazione isotonica. Performance pubblicate per campionato e
        nel tempo.
      </p>
      <h2>Limiti</h2>
      <p>
        Nessun modello è perfetto. Gli edge si riducono quando i bookmaker
        aggiornano; le informazioni su infortuni raggiungono i mercati più
        velocemente delle fonti pubbliche. Le performance passate non
        garantiscono risultati futuri.
      </p>
      <h2>Cadenza di retraining</h2>
      <p>
        Retraining walk-forward dei Pi-Ratings dopo ogni giornata; refit
        completo settimanale. Drift monitorato con test KS.
      </p>
    </>
  ),
  es: () => (
    <>
      <h2>El ensamble en 60 segundos</h2>
      <p>
        Cada partido se puntúa con tres modelos independientes — un Poisson
        Dixon-Coles, un clasificador CatBoost y un MLP PyTorch — cuyas
        probabilidades se combinan con una media ponderada optimizada por
        Dirichlet y se post-calibran con regresión isotónica. Las
        probabilidades finales se comparan con cuotas netas de margen; las
        value bets de valor esperado positivo se destacan y dimensionan con
        Kelly fraccionario.
      </p>
      <h2>Pi-Ratings (entrada)</h2>
      <p>
        Partimos de los Pi-Ratings de Constantinou y Fenton (2013), con
        componentes separadas para local y visitante, actualizadas tras cada
        partido.
      </p>
      <h2>Ingeniería de características</h2>
      <p>
        Más de 70 features por partido: diferenciales de rating, forma
        reciente, expected goals (xG) si están disponibles, priors de
        enfrentamientos directos, días de descanso, consenso de mercado,
        ventaja local por liga y más.
      </p>
      <h2>Calibración y honestidad</h2>
      <p>
        Seguimos Brier score, Ranked Probability Score (RPS) y Expected
        Calibration Error (ECE). Objetivo: ECE &lt; 1,5% tras post-calibración
        isotónica. Rendimiento publicado por liga y a lo largo del tiempo.
      </p>
      <h2>Limitaciones</h2>
      <p>
        Ningún modelo es perfecto. Las ventajas se reducen cuando las casas
        ajustan; la información de lesiones llega a los mercados más rápido
        que a las fuentes públicas. El rendimiento pasado no garantiza
        resultados futuros.
      </p>
      <h2>Cadencia de reentrenamiento</h2>
      <p>
        Reentrenamiento walk-forward de los Pi-Ratings tras cada jornada;
        refit completo semanal. Deriva monitorizada con test KS.
      </p>
    </>
  ),
};

export default function MethodologyPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const Body = CONTENT[locale];
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.methodology.title']}
      description={dict['page.methodology.description']}
      path="/methodology"
      lastUpdated={LAST_UPDATED}
      schemaType="Article"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.methodology.title'], path: '/methodology' },
      ]}
    >
      <Body />
    </EditorialPage>
  );
}
