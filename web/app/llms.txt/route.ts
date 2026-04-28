import { SITE_NAME, SITE_URL, absoluteUrl, localizedPath } from '@/lib/seo';
import { defaultLocale, locales } from '@/lib/i18n';
import { LEARN_SLUGS } from '@/content/learn';
import { GLOSSARY_ENTRIES } from '@/content/glossary/en';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type LeagueOut = { key: string; name: string };

async function fetchLeagues(): Promise<LeagueOut[]> {
  try {
    const res = await fetch(`${API_URL}/leagues`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    return (await res.json()) as LeagueOut[];
  } catch {
    return [];
  }
}

function bullet(label: string, path: string): string {
  return `- [${label}](${absoluteUrl(localizedPath(defaultLocale, path))})`;
}

export const revalidate = 3600;

export async function GET(): Promise<Response> {
  const leagues = await fetchLeagues();

  const lines: string[] = [];
  lines.push(`# ${SITE_NAME}`);
  lines.push('');
  lines.push(
    '> Independent, non-affiliate AI football match analytics. Calibrated probabilities and value bets for the Top 5 European leagues, powered by a CatBoost + Poisson + MLP ensemble.',
  );
  lines.push('');
  lines.push('## Core pages');
  lines.push(bullet('Today\'s predictions and value bets (includes homepage FAQ)', '/'));
  lines.push(bullet('League hub', '/leagues'));
  lines.push(bullet('Performance and accuracy tracker', '/performance'));
  lines.push(bullet('About — independent, non-affiliate AI football analytics', '/about'));
  lines.push(bullet('Methodology — model architecture, features and calibration', '/methodology'));
  lines.push(bullet('Glossary — canonical definitions of betting and AI terms', '/glossary'));
  lines.push('');
  lines.push('## Methodology signals');
  lines.push(
    '- Ensemble: CatBoost gradient boosting + Dixon-Coles Poisson + PyTorch MLP, blended with Dirichlet-tuned weights and isotonic-calibrated.',
  );
  lines.push(
    '- Staking: fractional Kelly (25–50% of full Kelly) on value bets with positive expected value after margin removal.',
  );
  lines.push(
    '- Transparency: every closed bet is tracked with ROI and Closing Line Value on the performance page.',
  );
  lines.push('');
  lines.push('## Responsible gambling');
  lines.push(bullet('Responsible gambling — helplines and self-exclusion tools', '/responsible-gambling'));
  lines.push('');
  lines.push('## Legal');
  lines.push(bullet('Terms of service', '/legal/terms'));
  lines.push(bullet('Privacy policy', '/legal/privacy'));
  lines.push(bullet('Cookie policy', '/legal/cookies'));
  lines.push('');
  if (leagues.length > 0) {
    lines.push('## Leagues');
    for (const l of leagues) {
      lines.push(bullet(`${l.name} predictions`, `/leagues/${l.key}`));
    }
    lines.push('');
  }
  lines.push('## Learn (educational pillar)');
  for (const slug of LEARN_SLUGS) {
    lines.push(bullet(slug.replace(/-/g, ' '), `/learn/${slug}`));
  }
  lines.push('');
  lines.push('## Glossary (canonical definitions)');
  for (const entry of GLOSSARY_ENTRIES) {
    lines.push(
      `- [${entry.term}](${absoluteUrl(
        localizedPath(defaultLocale, `/glossary/${entry.slug}`),
      )}): ${entry.shortDefinition}`,
    );
  }
  lines.push('');
  lines.push('## Localized variants');
  for (const locale of locales) {
    lines.push(`- ${locale.toUpperCase()}: ${absoluteUrl(localizedPath(locale, '/'))}`);
  }
  lines.push('');
  lines.push('## Sitemap');
  lines.push(`- ${SITE_URL.replace(/\/$/, '')}/sitemap.xml`);
  lines.push('');
  lines.push('## Full corpus (llms-full)');
  lines.push(
    `- [Full Markdown corpus](${SITE_URL.replace(/\/$/, '')}/llms-full.txt): glossary + Learn articles + homepage FAQ in a single file for AI ingestion`,
  );
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
