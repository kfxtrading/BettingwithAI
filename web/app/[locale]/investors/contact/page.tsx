import type { Metadata } from 'next';
import { EditorialPage } from '@/components/EditorialPage';
import { InvestorInquiryForm } from '@/components/InvestorInquiryForm';
import { buildMetadata } from '@/lib/seo';
import { getServerDictionary } from '@/lib/i18n/server';
import type { Locale } from '@/lib/i18n';

type PageProps = { params: { locale: Locale } };

const LAST_UPDATED = '2026-04-01';

export function generateMetadata({ params }: PageProps): Metadata {
  const { locale, dict } = getServerDictionary(params.locale);
  return buildMetadata({
    title: dict['page.investors.contact.title'],
    description: dict['page.investors.contact.description'],
    path: '/investors/contact',
    locale,
    ogType: 'article',
    noIndex: true,
  });
}

export default function InvestorContactPage({ params }: PageProps) {
  const { locale, dict } = getServerDictionary(params.locale);
  return (
    <EditorialPage
      locale={locale}
      title={dict['page.investors.contact.title']}
      description={dict['page.investors.contact.description']}
      path="/investors/contact"
      lastUpdated={LAST_UPDATED}
      schemaType="WebPage"
      breadcrumbs={[
        { name: 'Home', path: '/' },
        { name: dict['page.investors.title'], path: '/investors' },
        {
          name: dict['page.investors.contact.title'],
          path: '/investors/contact',
        },
      ]}
    >
      <p>{dict['page.investors.contact.intro']}</p>
      <div className="not-prose mt-6">
        <InvestorInquiryForm />
      </div>
    </EditorialPage>
  );
}
