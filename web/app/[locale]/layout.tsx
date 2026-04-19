import { notFound } from 'next/navigation';
import { locales, type Locale } from '@/lib/i18n';

export function generateStaticParams(): { locale: Locale }[] {
  return locales.map((locale) => ({ locale }));
}

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!(locales as readonly string[]).includes(params.locale)) {
    notFound();
  }
  return <>{children}</>;
}
