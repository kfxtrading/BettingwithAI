import type { Metadata } from 'next';
import Link from 'next/link';
import { EditorialPage } from '@/components/EditorialPage';
import { JsonLd } from '@/components/JsonLd';
import { KellyCalculator } from '@/components/KellyCalculator';
import {
  absoluteUrl,
  buildMetadata,
  faqPageLd,
  howToLd,
  localizedPath,
} from '@/lib/seo';
import { localizedHref } from '@/lib/localizedHref';
import { locales, type Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-25';

const TITLE = 'Kelly Calculator · Free Sports Betting Stake Sizer';
const DESCRIPTION =
  'Free interactive Kelly criterion calculator. Convert decimal, American or fractional odds and your win probability into a recommended stake. Includes fractional Kelly slider, expected value and edge over bookmaker.';

const KELLY_FAQS = [
  {
    question: 'What is the Kelly criterion?',
    answer:
      'A staking formula derived by John L. Kelly Jr. in 1956 that maximises long-term geometric growth of bankroll. Stake = (b·p − q) / b, where b = decimal_odds − 1, p is your win probability, q = 1 − p.',
  },
  {
    question: 'Why does the calculator default to half-Kelly?',
    answer:
      'Full Kelly assumes your probability is exact. Real-world models have noise; half-Kelly captures roughly 75% of long-term growth with about 50% of the volatility, which is the right trade-off for almost every retail bettor.',
  },
  {
    question: 'What if my odds are American or fractional?',
    answer:
      'Switch the format selector. The calculator converts American (+150 or -200) and fractional (5/2) odds to decimal internally before applying the Kelly formula.',
  },
  {
    question: 'Does the tool store my data?',
    answer:
      'No. The calculator runs entirely in your browser. Nothing is sent to a server, no cookies are set and no analytics events are recorded for this page.',
  },
];

export function generateStaticParams(): { locale: Locale }[] {
  return locales.map((locale) => ({ locale }));
}

export function generateMetadata({ params }: PageProps): Metadata {
  return buildMetadata({
    title: TITLE,
    description: DESCRIPTION,
    path: '/tools/kelly-calculator',
    locale: params.locale,
    ogType: 'website',
    keywords: [
      'Kelly calculator',
      'Kelly criterion calculator',
      'sports betting calculator',
      'fractional Kelly',
      'stake sizer',
      'expected value calculator',
      'value bet calculator',
    ],
  });
}

export default function KellyCalculatorPage({ params }: PageProps) {
  const { locale } = params;
  const url = absoluteUrl(localizedPath(locale, '/tools/kelly-calculator'));

  const webAppLd = {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: 'Kelly Calculator',
    url,
    applicationCategory: 'FinanceApplication',
    applicationSubCategory: 'Sports betting calculator',
    operatingSystem: 'All',
    isAccessibleForFree: true,
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    description: DESCRIPTION,
  };

  return (
    <EditorialPage
      locale={locale}
      title={TITLE}
      description={DESCRIPTION}
      path="/tools/kelly-calculator"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: 'Tools', path: '/tools/kelly-calculator' },
        { name: 'Kelly Calculator', path: '/tools/kelly-calculator' },
      ]}
    >
      <JsonLd
        data={[
          webAppLd,
          faqPageLd(KELLY_FAQS),
          howToLd({
            name: 'How to size a sports bet with the Kelly criterion',
            description:
              'Step-by-step guide to converting bookmaker odds and a calibrated win probability into a recommended fractional-Kelly stake.',
            totalTime: 'PT3M',
            url,
            steps: [
              {
                name: 'Pick the odds format',
                text: 'Switch the calculator between decimal (e.g. 2.10), American (+110, -120) and fractional (11/10) — all formats are converted to decimal internally.',
              },
              {
                name: 'Enter the bookmaker odds',
                text: 'Use the best available price across your bookmakers. Even small odds improvements compound meaningfully across hundreds of bets.',
              },
              {
                name: 'Enter your win probability',
                text: 'Use a calibrated probability from a model — not gut feel. The implied probability of the bookmaker odds is shown for comparison.',
              },
              {
                name: 'Set bankroll and Kelly fraction',
                text: 'Half-Kelly (50%) is the industry-standard default and captures roughly 75% of long-term growth at about 50% of the volatility of full Kelly.',
              },
              {
                name: 'Read the recommended stake',
                text: 'If the full Kelly stake is zero or negative, the bet is not value — pass. Otherwise, the slider returns the fractional-Kelly stake to wager.',
              },
            ],
          }),
        ]}
      />

      <p>
        Enter the bookmaker odds and your estimated win probability. The calculator
        returns the full Kelly stake, your fractional-Kelly stake (slider), the
        expected value of the bet and your edge over the bookmaker. Read the full{' '}
        <Link
          href={localizedHref(locale, '/learn/kelly-criterion')}
          hrefLang={locale}
          className="text-accent underline-offset-4 hover:underline"
        >
          Kelly criterion guide
        </Link>{' '}
        for the maths and worked examples.
      </p>

      <KellyCalculator />

      <section>
        <h2>How to use the calculator</h2>
        <ol className="list-decimal pl-5">
          <li>
            <strong>Pick odds format.</strong> Decimal (2.10), American (+110, -120)
            or fractional (11/10).
          </li>
          <li>
            <strong>Enter the bookmaker odds.</strong> Use the best available price
            across your books — even small odds improvements compound.
          </li>
          <li>
            <strong>Enter your win probability</strong> as a percentage. This is your
            calibrated model probability, not your gut feel.
          </li>
          <li>
            <strong>Set bankroll and Kelly fraction.</strong> 50% (half-Kelly) is the
            industry-standard starting point.
          </li>
          <li>
            <strong>Read the recommended stake.</strong> If full Kelly is zero or
            negative, the bet is not value — pass.
          </li>
        </ol>
      </section>

      <section>
        <h2>Frequently asked questions</h2>
        <dl className="space-y-4">
          {KELLY_FAQS.map((f) => (
            <div key={f.question}>
              <dt className="font-medium text-text">{f.question}</dt>
              <dd className="mt-1 text-muted">{f.answer}</dd>
            </div>
          ))}
        </dl>
      </section>
    </EditorialPage>
  );
}
