import type { Metadata, Viewport } from 'next';
import { GeistMono } from 'geist/font/mono';
import { GeistSans } from 'geist/font/sans';
import './globals.css';
import { Nav } from '@/components/Nav';
import { JsonLd } from '@/components/JsonLd';
import { Providers } from './providers';
import { SITE_NAME, SITE_URL, absoluteUrl, buildLanguageAlternates } from '@/lib/seo';
import { defaultLocale, locales, ogLocaleMap } from '@/lib/i18n';

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
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
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
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang={defaultLocale}
      className={`${GeistSans.variable} ${GeistMono.variable}`}
    >
      <head>
        <link rel="preconnect" href={API_URL} crossOrigin="anonymous" />
        <JsonLd data={[organizationLd, websiteLd]} />
      </head>
      <body className="min-h-screen bg-bg text-text antialiased">
        <Providers>
          <Nav />
          <main className="mx-auto w-full max-w-page px-6 pb-24 pt-10 md:px-12">
            {children}
          </main>
          <footer className="mx-auto w-full max-w-page px-6 pb-12 text-2xs text-muted md:px-12">
            <div className="hairline pt-6">
              Betting with AI · CatBoost + Poisson + MLP ensemble · Model v0.3
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
