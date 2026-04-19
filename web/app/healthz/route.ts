export const dynamic = 'force-static';

export function GET() {
  return new Response('ok', {
    status: 200,
    headers: { 'content-type': 'text/plain; charset=utf-8' },
  });
}

export function HEAD() {
  return new Response(null, { status: 200 });
}
