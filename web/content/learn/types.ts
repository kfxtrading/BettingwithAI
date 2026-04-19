import type { Locale } from '@/lib/i18n';

export type LearnSection = {
  heading: string;
  paragraphs: string[];
};

export type LearnFaq = {
  question: string;
  answer: string;
};

export type LearnArticle = {
  slug: string;
  title: string;
  description: string;
  /** ≤ 60-word abstract surfaced as the lead paragraph for AI Overviews. */
  tldr: string;
  sections: LearnSection[];
  faqs: LearnFaq[];
  lastUpdated: string;
  /** ISO 8601 date when the article was first published. */
  datePublished?: string;
};

export type LearnLibrary = Partial<Record<Locale, Record<string, LearnArticle>>>;
