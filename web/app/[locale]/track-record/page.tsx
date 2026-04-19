import type { Metadata } from 'next';
import { JsonLd } from '@/components/JsonLd';
import { CalibrationPlot, type CalibrationBucket } from '@/components/CalibrationPlot';
import { EditorialPage } from '@/components/EditorialPage';
import { absoluteUrl, buildMetadata, localizedPath, SITE_NAME, SITE_URL } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const LAST_UPDATED = new Date().toISOString().slice(0, 10);

type PageProps = { params: { locale: Locale } };

type CalibrationResponse = {
  league: string | null;
  n_records: number;
  n_settled: number;
  buckets: CalibrationBucket[];
};

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.trackRecord.title'],
    description: dict['page.trackRecord.description'],
    path: '/track-record',
    locale,
    ogType: 'article',
  });
}

async function fetchCalibration(): Promise<CalibrationResponse> {
  try {
    const res = await fetch(`${API_URL}/seo/track-record/calibration?bins=10`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error('upstream');
    return (await res.json()) as CalibrationResponse;
  } catch {
    return { league: null, n_records: 0, n_settled: 0, buckets: [] };
  }
}

export default async function TrackRecordPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  const data = await fetchCalibration();
  const csvUrl = `${SITE_URL.replace(/\/$/, '')}/api/track-record.csv`;

  const datasetLd = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `${SITE_NAME} prediction track record`,
    description:
      'Historical record of every Betting with AI football prediction with model probabilities, the actual result and a correctness flag. Updated after every matchday.',
    url: absoluteUrl(localizedPath(locale, '/track-record')),
    creator: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL },
    license: 'https://creativecommons.org/licenses/by/4.0/',
    isAccessibleForFree: true,
    keywords: [
      'football predictions',
      'AI accuracy',
      'calibration',
      'value bets',
      'Brier score',
      'RPS',
    ],
    distribution: [
      {
        '@type': 'DataDownload',
        encodingFormat: 'text/csv',
        contentUrl: csvUrl,
      },
    ],
    variableMeasured: [
      'prob_home',
      'prob_draw',
      'prob_away',
      'predicted_outcome',
      'actual_outcome',
      'correct',
    ],
    dateModified: LAST_UPDATED,
  };

  const breadcrumbs = [
    { name: 'Home', path: '/' },
    { name: 'Performance', path: '/performance' },
    { name: 'Track record', path: '/track-record' },
  ];

  return (
    <>
      <JsonLd data={datasetLd} />
      <EditorialPage
        locale={locale}
        title={dict['page.trackRecord.title']}
        description={dict['page.trackRecord.description']}
        path="/track-record"
        lastUpdated={LAST_UPDATED}
        breadcrumbs={breadcrumbs}
        schemaType="WebPage"
      >
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="surface-card px-4 py-3">
            <p className="text-2xs uppercase tracking-[0.08em] text-muted">
              {dict['trackRecord.stats.records']}
            </p>
            <p className="mt-1 font-mono text-lg text-text">{data.n_records}</p>
          </div>
          <div className="surface-card px-4 py-3">
            <p className="text-2xs uppercase tracking-[0.08em] text-muted">
              {dict['trackRecord.stats.settled']}
            </p>
            <p className="mt-1 font-mono text-lg text-text">{data.n_settled}</p>
          </div>
        </section>

        <section>
          <h2>{dict['trackRecord.calibration.title']}</h2>
          <p>{dict['trackRecord.calibration.caption']}</p>
          <CalibrationPlot buckets={data.buckets} />
        </section>

        <section>
          <h2>{dict['trackRecord.csv.title']}</h2>
          <p>{dict['trackRecord.csv.caption']}</p>
          <p>
            <a
              href={`${API_URL}/seo/track-record.csv`}
              download="track-record.csv"
              className="focus-ring inline-flex items-center gap-2 rounded-md border border-white/15 px-4 py-2 text-sm text-text hover:bg-white/5"
            >
              {dict['trackRecord.csv.button']}
            </a>
          </p>
        </section>
      </EditorialPage>
    </>
  );
}
