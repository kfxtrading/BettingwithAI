import type { DictionaryKey } from '@/lib/i18n';
import type { Outcome } from '@/lib/types';

interface BetLabelInput {
  outcome: Outcome;
  home_team: string;
  away_team: string;
}

export function localizedBetLabel(
  bet: BetLabelInput,
  t: (key: DictionaryKey) => string,
  teamName?: string,
): string {
  if (bet.outcome === 'D') return t('predictionCard.outcome.draw');
  const team =
    teamName ?? (bet.outcome === 'H' ? bet.home_team : bet.away_team);
  const outcomeKey: DictionaryKey =
    bet.outcome === 'H'
      ? 'predictionCard.outcome.home'
      : 'predictionCard.outcome.away';
  return `${team} ${t(outcomeKey)}`;
}
