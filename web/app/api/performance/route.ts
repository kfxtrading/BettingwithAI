import { NextResponse } from 'next/server';
import {
  fetchBankrollServer,
  fetchPerformanceSummaryServer,
} from '@/lib/server-api';

export const revalidate = 300;

export async function GET() {
  const [summary, bankroll] = await Promise.all([
    fetchPerformanceSummaryServer(),
    fetchBankrollServer(),
  ]);
  if (!summary) {
    return NextResponse.json(
      { error: 'upstream_unavailable' },
      { status: 503 },
    );
  }
  return NextResponse.json(
    { summary, bankroll },
    {
      headers: {
        'cache-control': 'public, s-maxage=300, stale-while-revalidate=900',
      },
    },
  );
}
