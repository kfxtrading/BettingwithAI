import en from './en';
import type { LearnArticle, LearnLibrary } from './types';
import type { Locale } from '@/lib/i18n';

export const LEARN_LIBRARY: LearnLibrary = {
  en,
};

/** Slug list to feed generateStaticParams. EN-only for now. */
export const LEARN_SLUGS: readonly string[] = Object.keys(en);

export function getArticle(
  locale: Locale,
  slug: string,
): LearnArticle | undefined {
  return LEARN_LIBRARY[locale]?.[slug] ?? LEARN_LIBRARY.en?.[slug];
}

export function listArticles(locale: Locale): LearnArticle[] {
  const lib = LEARN_LIBRARY[locale] ?? LEARN_LIBRARY.en ?? {};
  return Object.values(lib);
}
