import type { Metadata } from 'next';
import Link from 'next/link';
import { EditorialPage } from '@/components/EditorialPage';
import { buildMetadata } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import { localizedHref } from '@/lib/localizedHref';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-01';
const INVESTOR_EMAIL = 'investors@bettingwithai.app';

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.investors.title'],
    description: dict['page.investors.description'],
    path: '/investors',
    locale,
    ogType: 'article',
    noIndex: true,
  });
}

export default function InvestorsPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);

  const blocks: Array<{ title: string; body: string }> = [
    {
      title: dict['page.investors.block.product.title'],
      body: dict['page.investors.block.product.body'],
    },
    {
      title: dict['page.investors.block.market.title'],
      body: dict['page.investors.block.market.body'],
    },
    {
      title: dict['page.investors.block.stage.title'],
      body: dict['page.investors.block.stage.body'],
    },
  ];

  return (
    <EditorialPage
      locale={locale}
      title={dict['page.investors.title']}
      description={dict['page.investors.description']}
      path="/investors"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.investors.title'], path: '/investors' },
      ]}
    >
      <p>{dict['page.investors.intro']}</p>

      <div className="not-prose my-8 grid gap-4 md:grid-cols-3">
        {blocks.map((b) => (
          <div
            key={b.title}
            className="surface-card flex flex-col gap-2 px-5 py-4"
          >
            <h3 className="text-2xs uppercase tracking-[0.08em] text-muted">
              {b.title}
            </h3>
            <p className="text-sm leading-relaxed text-text">{b.body}</p>
          </div>
        ))}
      </div>

      <div className="not-prose mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Link
          href={localizedHref(locale, '/investors/contact')}
          hrefLang={locale}
          className="focus-ring press inline-flex items-center justify-center rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-bg"
        >
          {dict['page.investors.cta.requestAccess']}
        </Link>
        <span className="text-sm text-muted">
          {dict['page.investors.cta.emailLabel']}:{' '}
          <a
            href={`mailto:${INVESTOR_EMAIL}`}
            className="focus-ring underline hover:text-text"
          >
            {INVESTOR_EMAIL}
          </a>
        </span>
      </div>
    </EditorialPage>
  );
}
