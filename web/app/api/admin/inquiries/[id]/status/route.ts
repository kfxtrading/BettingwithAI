import { NextResponse, type NextRequest } from 'next/server';
import { requireOwnerReq } from '@/lib/accessAuth';
import { updateInquiryStatus, type InquiryStatus } from '@/lib/inquiries';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type RouteContext = { params: { id: string } };

const ALLOWED: InquiryStatus[] = ['new', 'replied', 'archived'];

export async function POST(request: NextRequest, { params }: RouteContext) {
  const owner = await requireOwnerReq(request);
  if (!owner) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  let body: { status?: unknown };
  try {
    body = (await request.json()) as { status?: unknown };
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }

  const next =
    typeof body.status === 'string' && ALLOWED.includes(body.status as InquiryStatus)
      ? (body.status as InquiryStatus)
      : null;
  if (!next) {
    return NextResponse.json({ error: 'validation' }, { status: 400 });
  }

  const updated = await updateInquiryStatus(params.id, next);
  if (!updated) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 });
  }
  return NextResponse.json({ ok: true });
}
