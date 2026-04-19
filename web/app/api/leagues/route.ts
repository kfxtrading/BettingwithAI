import { NextResponse } from 'next/server';
import {
  fetchLeagueSummariesServer,
  fetchLeaguesServer,
} from '@/lib/server-api';

export const revalidate = 3600;

export async function GET() {
  const [leagues, summaries] = await Promise.all([
    fetchLeaguesServer(),
    fetchLeagueSummariesServer(),
  ]);
  return NextResponse.json(
    { leagues, summaries },
    {
      headers: {
        'cache-control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    },
  );
}
