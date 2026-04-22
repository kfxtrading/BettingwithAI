import { NextResponse, type NextRequest } from 'next/server';
import { isAdminAuthenticatedReq } from '@/lib/adminAuth';
import { appendReply, getInquiry } from '@/lib/inquiries';
import { sendMail } from '@/lib/mailer';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type RouteContext = { params: { id: string } };

export async function POST(request: NextRequest, { params }: RouteContext) {
  if (!isAdminAuthenticatedReq(request)) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  let body: { subject?: unknown; body?: unknown };
  try {
    body = (await request.json()) as { subject?: unknown; body?: unknown };
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }

  const subject =
    typeof body.subject === 'string' ? body.subject.trim().slice(0, 300) : '';
  const text =
    typeof body.body === 'string' ? body.body.trim().slice(0, 5000) : '';
  if (!subject || !text) {
    return NextResponse.json({ error: 'validation' }, { status: 400 });
  }

  const inquiry = await getInquiry(params.id);
  if (!inquiry) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 });
  }

  const mailRes = await sendMail({
    to: inquiry.email,
    subject,
    text,
  });
  if (!mailRes.ok) {
    return NextResponse.json(
      { error: `mail_failed: ${mailRes.error}` },
      { status: 502 },
    );
  }

  const updated = await appendReply(params.id, { subject, body: text });
  if (!updated) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 });
  }

  return NextResponse.json({ ok: true, transport: mailRes.transport });
}
