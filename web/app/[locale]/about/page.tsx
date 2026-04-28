import type { Metadata } from 'next';
import Link from 'next/link';
import { EditorialPage } from '@/components/EditorialPage';
import { JsonLd } from '@/components/JsonLd';
import { absoluteUrl, buildMetadata, faqPageLd, localizedPath } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import { localizedHref } from '@/lib/localizedHref';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-28';
const DATE_PUBLISHED = '2026-04-01';

const ABOUT_FAQS = [
  {
    question: 'Is Betting with AI affiliated with any bookmaker?',
    answer:
      'No. We earn zero commission from bookmakers, do not run an affiliate programme, and do not accept wagers. Every prediction is published purely for educational purposes.',
  },
  {
    question: 'Who built this?',
    answer:
      'A solo data scientist with a background in sports analytics and machine learning. The codebase is open-source and the full methodology is publicly documented.',
  },
  {
    question: 'How is Betting with AI different from other prediction sites?',
    answer:
      'Most prediction sites are affiliate-driven: they earn revenue by directing users to bookmakers. We do not. We publish calibrated probabilities, a full track record, and our methodology — all without monetising through referrals.',
  },
  {
    question: 'Are the predictions financial advice?',
    answer:
      'No. This site is educational content only. We model football outcomes — we do not advise on whether or how much to bet.',
  },
  {
    question: 'What leagues do you cover?',
    answer:
      'The Top 5 European leagues: Premier League (England), Bundesliga (Germany), Serie A (Italy), La Liga (Spain) and Ligue 1 (France).',
  },
];

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.about.title'],
    description: dict['page.about.description'],
    path: '/about',
    locale,
    ogType: 'article',
    keywords: [
      'about betting with ai',
      'non-affiliate football predictions',
      'AI football analytics',
      'transparent football model',
      'independent prediction site',
    ],
  });
}

export default function AboutPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);

  const personLd = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: 'Betting with AI Team',
    jobTitle: 'Sports Data Scientist',
    knowsAbout: [
      'Machine Learning',
      'Sports Analytics',
      'Football Prediction',
      'Expected Goals',
      'Kelly Criterion',
    ],
    url: absoluteUrl(localizedPath(locale, '/about')),
    sameAs: [],
  };

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
        { name: 'About', path: '/about' },
      ]}
    >
      <JsonLd data={[personLd, faqPageLd(ABOUT_FAQS)]} />

      <section>
        <h2>Why this site exists</h2>
        <p>
          The football prediction industry is overwhelmingly driven by affiliate marketing.
          Sites publish &ldquo;tips&rdquo; — the most likely outcomes, not the most
          mispriced ones — and earn commission when users sign up to bookmakers via their
          links. The incentive is to generate traffic, not to be right.
        </p>
        <p>
          Betting with AI exists because we believe the right approach is the opposite:
          build a calibrated probabilistic model, publish every prediction publicly
          before kick-off, and then let the track record speak. No affiliate links. No
          hidden performance cherry-picking.
        </p>
      </section>

      <section>
        <h2>What we actually do</h2>
        <p>
          We build and maintain a three-component 1X2 ensemble for the Top 5 European
          leagues (Premier League, Bundesliga, Serie A, La Liga, Ligue 1):
        </p>
        <ul>
          <li>
            <strong>Dixon-Coles Poisson goal model</strong> — the 1997 bivariate Poisson
            with a low-score correction, updated every match-week.
          </li>
          <li>
            <strong>CatBoost classifier on 70+ features</strong> — rolling form,{' '}
            <Link
              href={localizedHref(locale, '/learn/pi-ratings-explained')}
              hrefLang={locale}
              className="text-accent underline-offset-4 hover:underline"
            >
              Pi-Ratings
            </Link>
            , expected goals, rest days, head-to-head, motivation flags.
          </li>
          <li>
            <strong>PyTorch MLP</strong> — a small three-layer network trained on the
            same feature matrix to capture non-linear interactions.
          </li>
        </ul>
        <p>
          All three outputs are blended with Dirichlet-tuned weights and post-calibrated
          with isotonic regression. The full methodology is documented on the{' '}
          <Link
            href={localizedHref(locale, '/methodology')}
            hrefLang={locale}
            className="text-accent underline-offset-4 hover:underline"
          >
            Methodology page
          </Link>
          .
        </p>
      </section>

      <section>
        <h2>How we measure ourselves</h2>
        <p>
          We refuse to use hit rate as a headline metric — picking favourites produces
          a 52% hit rate with no edge. Instead we track:
        </p>
        <ul>
          <li>
            <strong>RPS</strong> (Ranked Probability Score) — the gold-standard 1X2 metric.
          </li>
          <li>
            <strong>Brier score</strong> — mean squared error on the full probability vector.
          </li>
          <li>
            <strong>ECE</strong> (Expected Calibration Error) — distance from the diagonal
            on a reliability diagram.
          </li>
          <li>
            <strong>CLV</strong> (Closing Line Value) — the best leading indicator of
            long-run ROI. Read the{' '}
            <Link
              href={localizedHref(locale, '/learn/closing-line-value')}
              hrefLang={locale}
              className="text-accent underline-offset-4 hover:underline"
            >
              CLV explainer
            </Link>
            .
          </li>
        </ul>
        <p>
          Every metric is published per league on the{' '}
          <Link
            href={localizedHref(locale, '/performance')}
            hrefLang={locale}
            className="text-accent underline-offset-4 hover:underline"
          >
            Performance page
          </Link>
          , with a downloadable CSV of every prediction vs the actual result. There is
          no cherry-picking.
        </p>
      </section>

      <section>
        <h2>Our non-affiliate model</h2>
        <p>
          We earn nothing from bookmakers. We do not accept stakes, do not run a
          subscription service, and do not earn referral commission. The only revenue
          model compatible with honest probability forecasting is one that is entirely
          decoupled from bookmaker revenue — so that is what we built.
        </p>
        <p>
          This site is information only. Use it to understand probability, learn about
          football modelling, or cross-check your own analysis. Do not mistake model
          output for financial advice, and always gamble responsibly. See our{' '}
          <Link
            href={localizedHref(locale, '/responsible-gambling')}
            hrefLang={locale}
            className="text-accent underline-offset-4 hover:underline"
          >
            Responsible Gambling page
          </Link>{' '}
          for help and national helplines.
        </p>
      </section>

      <section>
        <h2>The technology stack</h2>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium text-text">ML backend</dt>
            <dd className="text-muted">Python 3.12, CatBoost, PyTorch, scikit-learn</dd>
          </div>
          <div>
            <dt className="font-medium text-text">API layer</dt>
            <dd className="text-muted">FastAPI, Pydantic v2, uvicorn</dd>
          </div>
          <div>
            <dt className="font-medium text-text">Frontend</dt>
            <dd className="text-muted">Next.js 14 App Router, TypeScript, Tailwind CSS</dd>
          </div>
          <div>
            <dt className="font-medium text-text">Infrastructure</dt>
            <dd className="text-muted">Railway (API + Docker), Vercel (frontend)</dd>
          </div>
          <div>
            <dt className="font-medium text-text">Data sources</dt>
            <dd className="text-muted">football-data.co.uk, Sofascore (opt-in), The Odds API</dd>
          </div>
          <div>
            <dt className="font-medium text-text">AI analyst</dt>
            <dd className="text-muted">Nomen — on-site AI football analyst powered by the model</dd>
          </div>
        </dl>
      </section>

      <section>
        <h2>Frequently asked questions</h2>
        <dl className="space-y-4">
          {ABOUT_FAQS.map((f) => (
            <div key={f.question}>
              <dt className="font-medium text-text">{f.question}</dt>
              <dd className="mt-1 text-muted">{f.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      <p className="text-2xs uppercase tracking-[0.08em] text-muted">
        Canonical URL: {absoluteUrl(localizedPath(locale, '/about'))}
      </p>
    </EditorialPage>
  );
}
