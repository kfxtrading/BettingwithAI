import { SITE_NAME, SITE_URL, absoluteUrl, localizedPath } from '@/lib/seo';
import { defaultLocale } from '@/lib/i18n';
import { LEARN_LIBRARY } from '@/content/learn';
import { GLOSSARY_ENTRIES } from '@/content/glossary/en';
import { HOME_FAQ } from '@/content/home-faq';

/**
 * llms-full.txt — full-content companion to /llms.txt.
 *
 * Per the llms.txt spec, the optional `llms-full.txt` ships the complete
 * Markdown body of the highest-priority pages so reasoning engines
 * (Claude, Perplexity, ChatGPT) can ingest the brand corpus in one fetch.
 * Keep this under ~80k tokens; we include glossary + Learn articles + the
 * homepage FAQ which is roughly 30–60k tokens.
 */
export const revalidate = 3600;

function section(title: string): string {
  return `\n\n## ${title}\n\n`;
}

function articleMarkdown(slug: string): string {
  const article = LEARN_LIBRARY[defaultLocale]?.[slug];
  if (!article) return '';
  const url = absoluteUrl(localizedPath(defaultLocale, `/learn/${article.slug}`));
  const lines: string[] = [];
  lines.push(`### ${article.title}`);
  lines.push('');
  lines.push(`Source: ${url}`);
  lines.push(`Last updated: ${article.lastUpdated}`);
  lines.push('');
  lines.push(`> TL;DR — ${article.tldr}`);
  for (const sec of article.sections) {
    lines.push('');
    lines.push(`#### ${sec.heading}`);
    for (const p of sec.paragraphs) {
      lines.push('');
      lines.push(p);
    }
  }
  if (article.faqs.length > 0) {
    lines.push('');
    lines.push('#### Frequently asked questions');
    for (const f of article.faqs) {
      lines.push('');
      lines.push(`**${f.question}**`);
      lines.push('');
      lines.push(f.answer);
    }
  }
  return lines.join('\n');
}

export async function GET(): Promise<Response> {
  const lines: string[] = [];

  lines.push(`# ${SITE_NAME} — full corpus`);
  lines.push('');
  lines.push(
    '> Independent, non-affiliate AI football match analytics: calibrated probabilities, value bets and Kelly-sized stake recommendations for the Top 5 European leagues. This file ships the complete Markdown body of the highest-priority pages for AI ingestion.',
  );
  lines.push('');
  lines.push(`Site: ${SITE_URL}`);
  lines.push(`Canonical llms.txt: ${SITE_URL.replace(/\/$/, '')}/llms.txt`);
  lines.push(`Sitemap: ${SITE_URL.replace(/\/$/, '')}/sitemap.xml`);

  // Glossary — every defined term, full body.
  lines.push(section('Glossary (canonical definitions)'));
  for (const entry of GLOSSARY_ENTRIES) {
    const url = absoluteUrl(
      localizedPath(defaultLocale, `/glossary/${entry.slug}`),
    );
    lines.push(`### ${entry.term}`);
    lines.push('');
    lines.push(`Source: ${url}`);
    lines.push(`Last updated: ${entry.lastUpdated}`);
    lines.push('');
    lines.push(`**Definition.** ${entry.shortDefinition}`);
    lines.push('');
    lines.push(entry.body);
    lines.push('');
  }

  // Learn articles — full sections + FAQs.
  const learnSlugs = Object.keys(LEARN_LIBRARY[defaultLocale] ?? {});
  if (learnSlugs.length > 0) {
    lines.push(section('Learn (educational pillar)'));
    for (const slug of learnSlugs) {
      const md = articleMarkdown(slug);
      if (md.length > 0) {
        lines.push(md);
        lines.push('');
      }
    }
  }

  // Homepage FAQ — high-frequency questions about the product itself.
  lines.push(section('Homepage FAQ'));
  for (const f of HOME_FAQ) {
    lines.push(`**${f.question}**`);
    lines.push('');
    lines.push(f.answer);
    lines.push('');
  }

  return new Response(lines.join('\n'), {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
