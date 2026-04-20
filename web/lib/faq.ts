import Fuse from 'fuse.js';
import type { DictionaryKey } from './i18n';

export interface FaqEntry {
  id: string;
  questionKey: DictionaryKey;
  answerKey: DictionaryKey;
  tags: string[];
}

export const FAQ_ENTRIES: FaqEntry[] = [
  {
    id: 'value-bet',
    questionKey: 'support.faq.valueBet.q',
    answerKey: 'support.faq.valueBet.a',
    tags: ['value', 'bet', 'edge', 'wette', 'wert', 'odds', 'quote', 'kelly'],
  },
  {
    id: 'accuracy',
    questionKey: 'support.faq.accuracy.q',
    answerKey: 'support.faq.accuracy.a',
    tags: [
      'accuracy',
      'genauigkeit',
      'model',
      'modell',
      'prediction',
      'vorhersage',
      'rps',
      'brier',
    ],
  },
  {
    id: 'data-source',
    questionKey: 'support.faq.dataSource.q',
    answerKey: 'support.faq.dataSource.a',
    tags: [
      'data',
      'daten',
      'source',
      'quelle',
      'football-data',
      'sofascore',
      'odds',
    ],
  },
  {
    id: 'snapshot-update',
    questionKey: 'support.faq.snapshotUpdate.q',
    answerKey: 'support.faq.snapshotUpdate.a',
    tags: [
      'snapshot',
      'update',
      'refresh',
      'aktualisierung',
      'time',
      'zeit',
      'wann',
    ],
  },
  {
    id: 'kelly',
    questionKey: 'support.faq.kelly.q',
    answerKey: 'support.faq.kelly.a',
    tags: ['kelly', 'stake', 'einsatz', 'bankroll', 'risk', 'risiko', 'staking'],
  },
  {
    id: 'pi-rating',
    questionKey: 'support.faq.piRating.q',
    answerKey: 'support.faq.piRating.a',
    tags: ['pi', 'rating', 'elo', 'strength', 'stärke', 'staerke', 'team'],
  },
  {
    id: 'responsible',
    questionKey: 'support.faq.responsible.q',
    answerKey: 'support.faq.responsible.a',
    tags: [
      'responsible',
      'verantwortung',
      'gambling',
      'spielsucht',
      'advice',
      'beratung',
      'financial',
    ],
  },
  {
    id: 'language',
    questionKey: 'support.faq.language.q',
    answerKey: 'support.faq.language.a',
    tags: ['language', 'sprache', 'locale', 'translation', 'übersetzung'],
  },
  {
    id: 'cookies',
    questionKey: 'support.faq.cookies.q',
    answerKey: 'support.faq.cookies.a',
    tags: ['cookie', 'cookies', 'consent', 'einwilligung', 'privacy', 'datenschutz'],
  },
  {
    id: 'contact',
    questionKey: 'support.faq.contact.q',
    answerKey: 'support.faq.contact.a',
    tags: ['contact', 'kontakt', 'email', 'support', 'hilfe', 'help'],
  },
];

export interface SearchableEntry {
  id: string;
  question: string;
  tags: string[];
}

export interface FaqMatch {
  entry: FaqEntry;
  score: number;
}

export function buildFuse(
  t: (key: DictionaryKey) => string,
): Fuse<SearchableEntry> {
  const searchable: SearchableEntry[] = FAQ_ENTRIES.map((e) => ({
    id: e.id,
    question: t(e.questionKey),
    tags: e.tags,
  }));
  return new Fuse(searchable, {
    keys: [
      { name: 'question', weight: 0.7 },
      { name: 'tags', weight: 0.3 },
    ],
    threshold: 0.45,
    includeScore: true,
    ignoreLocation: true,
    minMatchCharLength: 2,
  });
}

export function searchFaq(
  query: string,
  fuse: Fuse<SearchableEntry>,
): FaqMatch[] {
  const q = query.trim();
  if (!q) return [];
  const results = fuse.search(q).slice(0, 4);
  const byId = new Map(FAQ_ENTRIES.map((e) => [e.id, e]));
  const matches: FaqMatch[] = [];
  for (const r of results) {
    const entry = byId.get(r.item.id);
    if (entry) matches.push({ entry, score: r.score ?? 1 });
  }
  return matches;
}
