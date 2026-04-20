import type { Metadata, Viewport } from 'next';
import { GeistMono } from 'geist/font/mono';
import { GeistSans } from 'geist/font/sans';
import { Analytics } from '@vercel/analytics/next';
import './globals.css';
import { Nav } from '@/components/Nav';
import { CookieConsent } from '@/components/CookieConsent';
import { SupportChat } from '@/components/SupportChat';
import { JsonLd } from '@/components/JsonLd';
import { Providers } from './providers';
import { SITE_NAME, SITE_URL, absoluteUrl, buildLanguageAlternates } from '@/lib/seo';
import { defaultLocale, locales, ogLocaleMap } from '@/lib/i18n';
import { getServerLocale } from '@/lib/i18n/server';
import { Footer } from '@/components/Footer';
import { LeftRail } from '@/components/rail/LeftRail';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} · AI-driven football betting analyses`,
    template: `%s · ${SITE_NAME}`,
  },
  description:
    'Data-driven football predictions and value bets for the Premier League, Bundesliga, Serie A, La Liga and EFL Championship. CatBoost + Poisson + MLP ensemble with transparent performance tracking.',
  applicationName: SITE_NAME,
  category: 'sports',
  keywords: [
    'football predictions',
    'soccer predictions',
    'value bets',
    'AI betting',
    'Premier League predictions',
    'Bundesliga predictions',
    'Serie A predictions',
    'La Liga predictions',
    'EFL Championship predictions',
    'Pi-Ratings',
    'Poisson model',
    'CatBoost',
  ],
  authors: [{ name: SITE_NAME }],
  creator: SITE_NAME,
  publisher: SITE_NAME,
  alternates: {
    canonical: absoluteUrl('/'),
    languages: buildLanguageAlternates('/'),
  },
  openGraph: {
    type: 'website',
    url: absoluteUrl('/'),
    siteName: SITE_NAME,
    title: `${SITE_NAME} · AI-driven football betting analyses`,
    description:
      'Calibrated probabilities and value bets for the Top 5 football leagues — powered by a CatBoost + Poisson + MLP ensemble.',
    locale: ogLocaleMap[defaultLocale],
    alternateLocale: locales
      .filter((l) => l !== defaultLocale)
      .map((l) => ogLocaleMap[l]),
    images: [
      { url: absoluteUrl('/og.png'), width: 1200, height: 630, alt: SITE_NAME },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: `${SITE_NAME} · AI-driven football betting analyses`,
    description:
      'Calibrated probabilities and value bets for the Top 5 football leagues.',
    images: [absoluteUrl('/og.png')],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
  },
};

export const viewport: Viewport = {
  themeColor: '#0a0a0a',
  width: 'device-width',
  initialScale: 1,
};

const organizationLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: SITE_NAME,
  url: SITE_URL,
  logo: absoluteUrl('/og.png'),
};

const websiteLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: SITE_NAME,
  url: SITE_URL,
  inLanguage: ['en', 'de', 'fr', 'it', 'es'],
  description:
    'Data-driven football predictions and value bets for the Top 5 leagues.',
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: `${SITE_URL.replace(/\/$/, '')}/leagues?q={search_term_string}`,
    },
    'query-input': 'required name=search_term_string',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = getServerLocale();
  return (
    <html
      lang={locale}
      className={`${GeistSans.variable} ${GeistMono.variable}`}
    >
      <head>
        <link rel="preconnect" href={API_URL} crossOrigin="anonymous" />
        <JsonLd data={[organizationLd, websiteLd]} />
      </head>
      <body className="min-h-screen bg-bg text-text antialiased">
        <Providers initialLocale={locale}>
          <div className="lg:grid lg:grid-cols-[248px_minmax(0,1fr)] xl:grid-cols-[272px_minmax(0,1fr)]">
            <LeftRail />
            <div className="flex min-h-screen min-w-0 flex-col">
              <Nav />
              <main className="mx-auto w-full max-w-page px-6 pb-24 pt-10 md:px-12">
                {children}
              </main>
              <Footer />
            </div>
          </div>
          <CookieConsent />
          <SupportChat />
        </Providers>
        <Analytics />
      </body>
    </html>
  );
}
