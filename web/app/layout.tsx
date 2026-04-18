import type { Metadata } from 'next';
import { GeistMono } from 'geist/font/mono';
import { GeistSans } from 'geist/font/sans';
import './globals.css';
import { Nav } from '@/components/Nav';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Betting with AI',
  description:
    'Calm, data-driven betting analyses for the top 5 football leagues.',
  metadataBase: new URL('http://localhost:3000'),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
    >
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
