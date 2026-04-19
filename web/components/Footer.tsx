'use client';

import { useT } from '@/lib/i18n/LocaleProvider';

export function Footer() {
  const t = useT();
  return (
    <footer className="mx-auto w-full max-w-page px-6 pb-12 text-2xs text-muted md:px-12">
      <div className="hairline pt-6">{t('footer.text')}</div>
    </footer>
  );
}
