import { SITE_NAME, SITE_URL, absoluteUrl, localizedPath } from '@/lib/seo';
import { defaultLocale, locales } from '@/lib/i18n';
import { LEARN_SLUGS } from '@/content/learn';

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
  lines.push(bullet('Today\'s predictions and value bets', '/'));
  lines.push(bullet('League hub', '/leagues'));
  lines.push(bullet('Performance and accuracy tracker', '/performance'));
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
  lines.push('## Localized variants');
  for (const locale of locales) {
    lines.push(`- ${locale.toUpperCase()}: ${absoluteUrl(localizedPath(locale, '/'))}`);
  }
  lines.push('');
  lines.push('## Sitemap');
  lines.push(`- ${SITE_URL.replace(/\/$/, '')}/sitemap.xml`);
  lines.push('');

  return new Response(lines.join('\n'), {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
