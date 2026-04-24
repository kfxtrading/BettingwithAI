import type { Metadata } from 'next';
import {
  defaultLocale,
  hreflangRegions,
  locales,
  ogLocaleMap,
  type Locale,
} from './i18n';

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export const SITE_NAME = 'Betting with AI';

/**
 * Public sameAs profile URLs for the project / founder. Used by Organization
 * and Person JSON-LD to anchor the brand entity across the web (Wikidata,
 * Crunchbase, LinkedIn, X, GitHub, …). Configure via env vars so deployments
 * can override per environment without code changes.
 */
function readEnvList(name: string): string[] {
  const raw = process.env[name];
  if (!raw) return [];
  return raw
    .split(/[,\s]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

const ORG_SAME_AS_DEFAULT: readonly string[] = [
  'https://kirchhof.ai',
];

const PERSON_SAME_AS_DEFAULT: readonly string[] = [];

export const ORG_LEGAL_NAME =
  process.env.NEXT_PUBLIC_ORG_LEGAL_NAME ?? 'Kirchhof.ai';
export const ORG_FOUNDER_NAME =
  process.env.NEXT_PUBLIC_ORG_FOUNDER_NAME ?? 'Marcel Kirchhof';
export const ORG_FOUNDER_URL =
  process.env.NEXT_PUBLIC_ORG_FOUNDER_URL ?? absoluteUrl('/about');
export const ORG_LOGO_URL =
  process.env.NEXT_PUBLIC_ORG_LOGO_URL ?? absoluteUrl('/og.png');
export const ORG_LOCATION_LOCALITY =
  process.env.NEXT_PUBLIC_ORG_LOCALITY ?? 'Wiesenfelden';
export const ORG_LOCATION_REGION =
  process.env.NEXT_PUBLIC_ORG_REGION ?? 'Bavaria';
export const ORG_LOCATION_COUNTRY =
  process.env.NEXT_PUBLIC_ORG_COUNTRY ?? 'DE';

export function orgSameAs(): readonly string[] {
  const fromEnv = readEnvList('NEXT_PUBLIC_ORG_SAMEAS');
  return fromEnv.length > 0 ? fromEnv : ORG_SAME_AS_DEFAULT;
}

export function personSameAs(): readonly string[] {
  const fromEnv = readEnvList('NEXT_PUBLIC_PERSON_SAMEAS');
  return fromEnv.length > 0 ? fromEnv : PERSON_SAME_AS_DEFAULT;
}

/**
 * Schema.org Organization JSON-LD describing the publisher entity.
 * Includes founder, logo, location and sameAs to anchor the brand
 * across the web for Generative Engine Optimization (GEO).
 */
export function organizationLd(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: SITE_NAME,
    legalName: ORG_LEGAL_NAME,
    url: SITE_URL,
    logo: ORG_LOGO_URL,
    description:
      'Independent publisher of AI-driven football match analytics: calibrated probabilities, value bets and Kelly-sized stake recommendations for the Top 5 European leagues.',
    foundingDate: process.env.NEXT_PUBLIC_ORG_FOUNDING_DATE,
    founder: {
      '@type': 'Person',
      name: ORG_FOUNDER_NAME,
      url: ORG_FOUNDER_URL,
      jobTitle: 'Founder',
      sameAs: personSameAs(),
    },
    address: {
      '@type': 'PostalAddress',
      addressLocality: ORG_LOCATION_LOCALITY,
      addressRegion: ORG_LOCATION_REGION,
      addressCountry: ORG_LOCATION_COUNTRY,
    },
    sameAs: orgSameAs(),
  };
}

/** Schema.org Person JSON-LD for the founder / About page. */
export function personLd(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: ORG_FOUNDER_NAME,
    url: ORG_FOUNDER_URL,
    jobTitle: 'Founder',
    worksFor: {
      '@type': 'Organization',
      name: ORG_LEGAL_NAME,
      url: SITE_URL,
    },
    sameAs: personSameAs(),
  };
}

type HowToStep = { name: string; text: string; url?: string };
type HowToInput = {
  name: string;
  description: string;
  steps: readonly HowToStep[];
  totalTime?: string;
  url?: string;
};

/** Schema.org HowTo JSON-LD for tutorial / step-by-step pages. */
export function howToLd(input: HowToInput): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: input.name,
    description: input.description,
    ...(input.totalTime ? { totalTime: input.totalTime } : {}),
    ...(input.url ? { url: input.url } : {}),
    step: input.steps.map((step, i) => ({
      '@type': 'HowToStep',
      position: i + 1,
      name: step.name,
      text: step.text,
      ...(step.url ? { url: step.url } : {}),
    })),
  };
}

type ArticleInput = {
  headline: string;
  description: string;
  url: string;
  datePublished: string;
  dateModified: string;
  authorName?: string;
  authorUrl?: string;
  image?: string;
  inLanguage?: string;
};

/** Schema.org Article JSON-LD for blog posts and editorial content. */
export function articleLd(input: ArticleInput): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: input.headline,
    description: input.description,
    url: input.url,
    datePublished: input.datePublished,
    dateModified: input.dateModified,
    inLanguage: input.inLanguage ?? 'en',
    author: {
      '@type': 'Person',
      name: input.authorName ?? ORG_FOUNDER_NAME,
      url: input.authorUrl ?? ORG_FOUNDER_URL,
    },
    publisher: {
      '@type': 'Organization',
      name: ORG_LEGAL_NAME,
      url: SITE_URL,
      logo: { '@type': 'ImageObject', url: ORG_LOGO_URL },
    },
    image: input.image ?? absoluteUrl('/og.png'),
    mainEntityOfPage: input.url,
  };
}

type SportsEventInput = {
  homeTeam: string;
  awayTeam: string;
  startDate: string;
  url?: string;
  venueName?: string;
  venueAddress?: string;
  status?:
    | 'EventScheduled'
    | 'EventPostponed'
    | 'EventCancelled'
    | 'EventMovedOnline'
    | 'EventRescheduled';
};

/** Schema.org SportsEvent JSON-LD for match-preview pages. */
export function sportsEventLd(input: SportsEventInput): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'SportsEvent',
    name: `${input.homeTeam} vs ${input.awayTeam}`,
    sport: 'Association football',
    startDate: input.startDate,
    eventStatus: `https://schema.org/${input.status ?? 'EventScheduled'}`,
    homeTeam: { '@type': 'SportsTeam', name: input.homeTeam },
    awayTeam: { '@type': 'SportsTeam', name: input.awayTeam },
    ...(input.url ? { url: input.url } : {}),
    ...(input.venueName
      ? {
          location: {
            '@type': 'Place',
            name: input.venueName,
            ...(input.venueAddress ? { address: input.venueAddress } : {}),
          },
        }
      : {}),
  };
}

/** Schema.org JSON-LD snippet describing the product as a SoftwareApplication. */
export function softwareApplicationLd(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: SITE_NAME,
    url: SITE_URL,
    applicationCategory: 'SportsApplication',
    applicationSubCategory: 'Football analytics',
    operatingSystem: 'Web',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    description:
      'AI-driven football match analytics with calibrated probabilities, value bet detection and Kelly-sized stake recommendations for the Top 5 European leagues.',
    featureList: [
      'Calibrated 1X2 probabilities',
      'Value bet detection (positive expected value)',
      'Pi-Ratings and Poisson goal model',
      'CatBoost + MLP ensemble',
      'Kelly criterion stake sizing',
      'Walk-forward performance tracking',
    ],
    image: absoluteUrl('/og.png'),
    isAccessibleForFree: true,
    publisher: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL },
  };
}

/** Schema.org JSON-LD snippet describing the product as a WebApplication. */
export function webApplicationLd(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: SITE_NAME,
    url: SITE_URL,
    browserRequirements: 'Requires a modern browser with JavaScript enabled.',
    applicationCategory: 'SportsApplication',
    operatingSystem: 'All',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    isAccessibleForFree: true,
  };
}

type FaqQa = { question: string; answer: string };

/** Schema.org FAQPage JSON-LD from a list of Q&A. */
export function faqPageLd(qa: readonly FaqQa[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: qa.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  };
}

type DefinedTermInput = {
  term: string;
  description: string;
  url: string;
  termCode?: string;
  inDefinedTermSet?: string;
};

/** Schema.org DefinedTerm JSON-LD for glossary entries. */
export function definedTermLd(input: DefinedTermInput): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'DefinedTerm',
    name: input.term,
    description: input.description,
    url: input.url,
    ...(input.termCode ? { termCode: input.termCode } : {}),
    inDefinedTermSet:
      input.inDefinedTermSet ?? absoluteUrl('/en/glossary'),
  };
}

/**
 * Strip a leading locale segment (e.g. "/en/leagues" -> "/leagues").
 * Returns the path unchanged when it does not start with a known locale.
 */
export function stripLocale(path: string): string {
  const m = path.match(/^\/([a-z]{2})(?=\/|$)/i);
  if (m && (locales as readonly string[]).includes(m[1].toLowerCase())) {
    const rest = path.slice(m[0].length);
    return rest.length === 0 ? '/' : rest;
  }
  return path.startsWith('/') ? path : `/${path}`;
}

/**
 * Build a locale-prefixed path. `path` should be locale-agnostic
 * (e.g. "/", "/leagues", "/leagues/PL"). The locale is always
 * prepended, so `/` becomes `/en` and `/leagues` becomes `/en/leagues`.
 */
export function localizedPath(locale: Locale, path = '/'): string {
  const cleaned = stripLocale(path);
  if (cleaned === '/') return `/${locale}`;
  return `/${locale}${cleaned}`;
}

export function absoluteUrl(path = '/'): string {
  const base = SITE_URL.replace(/\/$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

/**
 * Build hreflang alternates for a locale-agnostic path.
 * Each entry maps a BCP-47 tag to the absolute URL of the
 * matching localized variant. Includes `x-default` -> default locale.
 */
export function buildLanguageAlternates(
  path = '/',
): Record<string, string> {
  const alternates: Record<string, string> = {};
  for (const [tag, locale] of Object.entries(hreflangRegions)) {
    alternates[tag] = absoluteUrl(localizedPath(locale, path));
  }
  alternates['x-default'] = absoluteUrl(localizedPath(defaultLocale, path));
  return alternates;
}

type BuildMetadataInput = {
  title: string;
  description: string;
  /** Locale-agnostic path (without `/en`, `/de` etc. prefix). */
  path?: string;
  locale?: Locale;
  keywords?: string[];
  ogType?: 'website' | 'article';
  /** When true, emit `noindex, follow` robots directives. */
  noIndex?: boolean;
};

export function buildMetadata({
  title,
  description,
  path = '/',
  locale = defaultLocale,
  keywords,
  ogType = 'website',
  noIndex = false,
}: BuildMetadataInput): Metadata {
  const canonicalPath = localizedPath(locale, path);
  const url = absoluteUrl(canonicalPath);
  return {
    title,
    description,
    keywords,
    robots: noIndex
      ? {
          index: false,
          follow: true,
          nocache: true,
          googleBot: {
            index: false,
            follow: true,
            noimageindex: true,
            'max-snippet': 0,
            'max-image-preview': 'none',
          },
        }
      : undefined,
    alternates: noIndex
      ? { canonical: url }
      : {
          canonical: url,
          languages: buildLanguageAlternates(path),
        },
    openGraph: {
      type: ogType,
      url,
      title,
      description,
      siteName: SITE_NAME,
      locale: ogLocaleMap[locale],
      alternateLocale: locales
        .filter((l) => l !== locale)
        .map((l) => ogLocaleMap[l]),
      images: [
        { url: absoluteUrl('/og.png'), width: 1200, height: 630, alt: SITE_NAME },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [absoluteUrl('/og.png')],
    },
  };
}
