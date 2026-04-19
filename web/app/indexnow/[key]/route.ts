import { notFound } from 'next/navigation';

const INDEXNOW_KEY = process.env.INDEXNOW_KEY ?? '';

/**
 * IndexNow ownership-verification endpoint.
 *
 * IndexNow requires the key to be served at `/{key}.txt` containing
 * the same key as plain text. We accept both `/<key>` and `/<key>.txt`.
 */
export async function GET(
  _req: Request,
  { params }: { params: { key: string } },
): Promise<Response> {
  if (!INDEXNOW_KEY) notFound();
  const key = (params.key ?? '').replace(/\.txt$/i, '');
  if (key !== INDEXNOW_KEY) notFound();
  return new Response(INDEXNOW_KEY, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=86400',
    },
  });
}
