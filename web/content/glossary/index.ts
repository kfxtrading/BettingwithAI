import type { Locale } from '@/lib/i18n';
import {
  GLOSSARY_ENTRIES as EN_ENTRIES,
  GLOSSARY_SLUGS,
  type GlossaryEntry,
} from './en';
import DE_ENTRIES from './de';
import FR_ENTRIES from './fr';
import IT_ENTRIES from './it';
import ES_ENTRIES from './es';

export type { GlossaryEntry };
export { GLOSSARY_SLUGS };

const LOCALE_ENTRIES: Record<string, readonly GlossaryEntry[]> = {
  en: EN_ENTRIES,
  de: DE_ENTRIES,
  fr: FR_ENTRIES,
  it: IT_ENTRIES,
  es: ES_ENTRIES,
};

export function getLocalizedGlossaryEntries(
  locale: Locale,
): readonly GlossaryEntry[] {
  return LOCALE_ENTRIES[locale] ?? EN_ENTRIES;
}

export function getLocalizedGlossaryEntry(
  locale: Locale,
  slug: string,
): GlossaryEntry | undefined {
  const entries = LOCALE_ENTRIES[locale] ?? EN_ENTRIES;
  return entries.find((e) => e.slug === slug) ?? EN_ENTRIES.find((e) => e.slug === slug);
}

// Re-export English helpers for backward-compat
export { GLOSSARY_ENTRIES, getGlossaryEntry } from './en';
