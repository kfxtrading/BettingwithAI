import type { Metadata } from 'next';
import Link from 'next/link';
import { EditorialPage } from '@/components/EditorialPage';
import { JsonLd } from '@/components/JsonLd';
import { absoluteUrl, buildMetadata, faqPageLd, localizedPath } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import { localizedHref } from '@/lib/localizedHref';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-25';
const DATE_PUBLISHED = '2026-04-25';

const METHODOLOGY_FAQS = [
  {
    question: 'What model architecture does Betting with AI use?',
    answer:
      'A three-component ensemble: (1) a Dixon-Coles Poisson goal model, (2) a CatBoost gradient-boosted classifier on 70+ engineered features, and (3) a PyTorch MLP. Their probabilities are blended with Dirichlet-tuned weights and post-calibrated with isotonic regression.',
  },
  {
    question: 'What data sources feed the model?',
    answer:
      'Historical CSV match data from football-data.co.uk for the Top 5 European leagues (Premier League, Bundesliga, Serie A, La Liga, Ligue 1) plus opt-in Sofascore xG and lineups. Closing 1X2 odds are used to compute Closing Line Value (CLV).',
  },
  {
    question: 'Which KPIs do you publish?',
    answer:
      'Ranked Probability Score (RPS), Brier score, log-loss, accuracy, Expected Calibration Error (ECE) and CLV per league. The walk-forward backtest and reliability diagram are public on the Performance page.',
  },
  {
    question: 'What are the limitations?',
    answer:
      'The model does not see in-game injuries that emerge after lineup release, weighting of cup-fixture motivation, or referee-specific tendencies. Predictions are educational and never financial advice.',
  },
  {
    question: 'How often is the model retrained?',
    answer:
      'Walk-forward retraining runs every match-week. We freeze a model snapshot per season and report metrics on out-of-sample folds only — there is no peeking at future data.',
  },
];

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.methodology.title'],
    description: dict['page.methodology.description'],
    path: '/methodology',
    locale,
    ogType: 'article',
    keywords: [
      'football prediction methodology',
      'CatBoost ensemble',
      'Dixon-Coles Poisson',
      'isotonic calibration',
      'pi-ratings',
      'walk-forward backtest',
      'RPS Brier ECE CLV',
    ],
  });
}

export default function MethodologyPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);

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
        { name: 'Methodology', path: '/methodology' },
      ]}
    >
      <JsonLd data={faqPageLd(METHODOLOGY_FAQS)} />

      <aside className="not-prose rounded-md border border-white/10 bg-white/5 p-4">
        <p className="m-0 text-2xs uppercase tracking-[0.08em] text-muted">TL;DR</p>
        <p className="mt-2 m-0 text-sm leading-relaxed text-text">
          Our 1X2 probabilities come from a three-model ensemble — Dixon-Coles Poisson,
          CatBoost on 70+ features, and a PyTorch MLP — blended with Dirichlet-tuned
          weights and post-calibrated with isotonic regression. We measure performance
          with RPS, Brier, ECE and CLV in a public walk-forward backtest.
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">Model version</dt>
            <dd className="mt-1 font-mono text-text">v0.3</dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">Leagues covered</dt>
            <dd className="mt-1 font-mono text-text">Top 5 EU</dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">Calibration</dt>
            <dd className="mt-1 font-mono text-text">Isotonic + Platt</dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">Backtest</dt>
            <dd className="mt-1 font-mono text-text">Walk-forward</dd>
          </div>
        </dl>
      </aside>

      <section>
        <h2>Model architecture</h2>
        <p>
          Betting with AI is a three-component probabilistic ensemble for the Home /
          Draw / Away (1X2) market. Each component is trained independently and their
          predictions are blended with Dirichlet-tuned weights tuned on a hold-out
          validation season.
        </p>
        <h3>1. Dixon-Coles Poisson goal model</h3>
        <p>
          A bivariate Poisson with the classic 1997 Dixon-Coles low-score correction.
          Each team has separate home and away attack/defence strengths, decayed with
          an exponential half-life of about 60 days so recent results count more.
          Outputs an exact-score matrix from which we derive 1X2, Over/Under and BTTS
          probabilities.
        </p>
        <h3>2. CatBoost classifier on engineered features</h3>
        <p>
          Gradient-boosted decision trees on 70+ features: rolling form, Pi-Ratings,
          xG-for and xG-against, rest days, head-to-head, league averages, motivation
          flags, and (when scraping is enabled) Sofascore lineups. CatBoost handles
          categorical features without one-hot encoding and is robust to mild noise.
        </p>
        <h3>3. PyTorch MLP</h3>
        <p>
          A small 3-layer multilayer perceptron trained on the same feature matrix,
          regularised with dropout and label-smoothing. The MLP captures non-monotonic
          interactions that boosting sometimes misses.
        </p>
        <h3>Ensembling and calibration</h3>
        <p>
          Component probability vectors are blended with weights {`(w_p, w_c, w_m)`}{' '}
          fitted via a Dirichlet posterior on validation log-loss. The blended
          probabilities are then passed through per-class isotonic regression (Platt
          scaling as a fallback). After calibration, Expected Calibration Error (ECE)
          on the hold-out is below 1.5%.
        </p>
      </section>

      <section>
        <h2>Data and feature pipeline</h2>
        <ul>
          <li>
            <strong>Match results &amp; odds:</strong> football-data.co.uk historical
            CSVs for the Top 5 leagues (Premier League, Bundesliga, Serie A, La Liga,
            Ligue 1), including opening and closing 1X2 odds.
          </li>
          <li>
            <strong>Pi-Ratings:</strong> separate home/away strengths updated after
            every match using a learning-rate-decayed rule (Constantinou &amp; Fenton,
            2013). Read the full{' '}
            <Link
              href={localizedHref(locale, '/learn/pi-ratings-explained')}
              hrefLang={locale}
              className="text-accent underline-offset-4 hover:underline"
            >
              pi-ratings explainer
            </Link>
            .
          </li>
          <li>
            <strong>xG and lineups (optional):</strong> opt-in async Sofascore client
            with a 25-second token-bucket rate-limit and 24-hour SQLite TTL cache. We
            never call the source without an explicit{' '}
            <code>SCRAPING_ENABLED=1</code> flag.
          </li>
          <li>
            <strong>Closing odds for CLV:</strong> Pinnacle closing line is the gold
            standard; we record it for every prediction we publish.
          </li>
        </ul>
      </section>

      <section>
        <h2>Key Performance Indicators (KPIs)</h2>
        <p>
          We refuse to use hit-rate as a headline metric — it is misleading for
          probabilistic models. Instead we publish:
        </p>
        <ul>
          <li>
            <strong>RPS</strong> (Ranked Probability Score) — gold-standard 1X2 metric
            that penalises confident wrong predictions on adjacent outcomes less than
            on opposite outcomes.
          </li>
          <li>
            <strong>Brier score</strong> — mean squared error between predicted vector
            and one-hot actual outcome.
          </li>
          <li>
            <strong>Log-loss</strong> — strictly proper scoring rule used for
            ensemble-weight tuning.
          </li>
          <li>
            <strong>ECE</strong> (Expected Calibration Error) — average distance of a
            reliability diagram from the diagonal.
          </li>
          <li>
            <strong>CLV</strong> (Closing Line Value) — best leading indicator of
            long-term ROI. Mean CLV converges in ≈ 200 bets, while raw ROI takes
            thousands.
          </li>
        </ul>
        <p>
          All five are published on the{' '}
          <Link
            href={localizedHref(locale, '/performance')}
            hrefLang={locale}
            className="text-accent underline-offset-4 hover:underline"
          >
            Performance page
          </Link>{' '}
          per league.
        </p>
      </section>

      <section>
        <h2>Walk-forward backtest</h2>
        <p>
          We never evaluate on data the model has seen. The backtest expands the
          training window match-week by match-week: train on weeks 1…N, predict week
          N+1, log results, then retrain. This mirrors live deployment exactly and
          eliminates look-ahead bias.
        </p>
        <p>
          We additionally run a Kolmogorov-Smirnov drift test on the feature
          distribution every match-week and flag any feature whose KS distance versus
          the training set exceeds 0.10.
        </p>
      </section>

      <section>
        <h2>Limitations</h2>
        <ul>
          <li>
            <strong>Late-breaking news.</strong> Injuries, suspensions or tactical
            changes that emerge after our last data refresh are not reflected.
          </li>
          <li>
            <strong>Cup motivation.</strong> Dead-rubber and rotation effects are
            modelled crudely; values for low-stakes fixtures should be treated with
            extra scepticism.
          </li>
          <li>
            <strong>Small leagues.</strong> The model is trained on the Top 5 leagues
            only; performance outside that scope is not validated.
          </li>
          <li>
            <strong>Variance.</strong> Even a perfectly calibrated model can produce
            30–50% drawdowns at full Kelly. Use fractional Kelly and bankroll caps.
          </li>
          <li>
            <strong>Educational content.</strong> Nothing on this site is financial
            advice. We do not accept stakes, do not run an affiliate programme, and do
            not earn commission from bookmakers.
          </li>
        </ul>
      </section>

      <section>
        <h2>Reproducibility &amp; transparency</h2>
        <p>
          The model code is open-source. Every published prediction is logged with the
          model version, feature snapshot and component probabilities so that any
          third party can reproduce the result. The full track-record CSV is
          downloadable from the Performance page.
        </p>
        <p>
          Try the{' '}
          <Link
            href={localizedHref(locale, '/tools/kelly-calculator')}
            hrefLang={locale}
            className="text-accent underline-offset-4 hover:underline"
          >
            Kelly calculator
          </Link>{' '}
          to size a stake from your own probability and the bookmaker odds.
        </p>
      </section>

      <section>
        <h2>Frequently asked questions</h2>
        <dl className="space-y-4">
          {METHODOLOGY_FAQS.map((f) => (
            <div key={f.question}>
              <dt className="font-medium text-text">{f.question}</dt>
              <dd className="mt-1 text-muted">{f.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      <p className="text-2xs uppercase tracking-[0.08em] text-muted">
        Canonical URL: {absoluteUrl(localizedPath(locale, '/methodology'))}
      </p>
    </EditorialPage>
  );
}
