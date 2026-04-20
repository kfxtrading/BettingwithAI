import { revalidatePath } from 'next/cache';
import { NextResponse, type NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

type Body = { paths?: unknown };

export async function POST(request: NextRequest) {
  const expected = process.env.REVALIDATE_TOKEN;
  if (!expected) {
    return NextResponse.json(
      { error: 'revalidate_disabled' },
      { status: 503 },
    );
  }
  const token = request.headers.get('x-revalidate-token') ?? '';
  if (token !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  let body: Body;
  try {
    body = (await request.json()) as Body;
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }

  const raw = Array.isArray(body.paths) ? body.paths : [];
  const paths = raw.filter(
    (p): p is string => typeof p === 'string' && p.startsWith('/'),
  );
  if (paths.length === 0) {
    return NextResponse.json({ error: 'no_paths' }, { status: 400 });
  }

  const revalidated: string[] = [];
  const failed: { path: string; error: string }[] = [];
  for (const p of paths) {
    try {
      revalidatePath(p, 'page');
      revalidated.push(p);
    } catch (err) {
      failed.push({ path: p, error: String(err) });
    }
  }
  return NextResponse.json({ revalidated, failed });
}
