'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Section } from '@/components/Section';
import { RatingsTable } from '@/components/RatingsTable';
import { Empty } from '@/components/Empty';
import { api, queryKeys } from '@/lib/api';
import type { FormRow } from '@/lib/types';
import { useLocale } from '@/lib/i18n/LocaleProvider';

type Props = {
  leagueKey: string;
  leagueName: string;
};

export function LeagueClient({ leagueKey, leagueName }: Props) {
  const { t } = useLocale();
  const ratingsQuery = useQuery({
    queryKey: queryKeys.ratings(leagueKey, 24),
    queryFn: () => api.ratings(leagueKey, 24),
    enabled: leagueKey.length > 0,
  });
  const formQuery = useQuery({
    queryKey: queryKeys.form(leagueKey, 50),
    queryFn: () => api.form(leagueKey, 50),
    enabled: leagueKey.length > 0,
  });

  const formMap: Record<string, FormRow> = {};
  for (const row of formQuery.data ?? []) {
    formMap[row.team] = row;
  }

  return (
    <>
      <header className="flex flex-col gap-3">
        <Link
          href="/leagues"
          className="focus-ring text-2xs uppercase tracking-[0.12em] text-muted hover:text-text"
        >
          {t('league.back')}
        </Link>
        <h1 className="text-2xl font-medium tracking-tight">{leagueName}</h1>
        <p className="text-sm text-muted">{t('league.subtitle')}</p>
      </header>

      <Section title={t('league.section.table')}>
        {ratingsQuery.isLoading ? (
          <div className="surface-card h-96 animate-pulse" />
        ) : ratingsQuery.isError || (ratingsQuery.data?.length ?? 0) === 0 ? (
          <Empty
            title={t('league.empty.title')}
            hint={t('league.empty.hint')}
          />
        ) : (
          <RatingsTable rows={ratingsQuery.data ?? []} forms={formMap} />
        )}
      </Section>
    </>
  );
}
