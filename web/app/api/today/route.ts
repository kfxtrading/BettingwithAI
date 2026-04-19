import { NextResponse, type NextRequest } from 'next/server';
import { fetchTodayServer } from '@/lib/server-api';

export const revalidate = 60;

export async function GET(request: NextRequest) {
  const league = request.nextUrl.searchParams.get('league') ?? undefined;
  const data = await fetchTodayServer(league);
  if (!data) {
    return NextResponse.json(
      { error: 'upstream_unavailable' },
      { status: 503 },
    );
  }
  return NextResponse.json(data, {
    headers: {
      'cache-control': 'public, s-maxage=60, stale-while-revalidate=300',
    },
  });
}
