import { NextResponse, type NextRequest } from 'next/server';
import { addInquiry, type InquiryInput } from '@/lib/inquiries';
import { sendMail } from '@/lib/mailer';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

const MAX_FIELD = 300;
const MAX_MESSAGE = 2000;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type RateBucket = { count: number; resetAt: number };
const rateLimit = new Map<string, RateBucket>();
const RATE_WINDOW_MS = 60 * 60 * 1000;
const RATE_MAX = 5;

function clientIp(req: NextRequest): string {
  const fwd = req.headers.get('x-forwarded-for');
  if (fwd) return fwd.split(',')[0].trim();
  return req.headers.get('x-real-ip') ?? 'unknown';
}

function withinRateLimit(ip: string): boolean {
  const now = Date.now();
  const bucket = rateLimit.get(ip);
  if (!bucket || bucket.resetAt < now) {
    rateLimit.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return true;
  }
  if (bucket.count >= RATE_MAX) return false;
  bucket.count += 1;
  return true;
}

function clean(value: unknown, max: number): string {
  if (typeof value !== 'string') return '';
  return value.trim().slice(0, max);
}

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }

  const honeypot = typeof body.website === 'string' ? body.website : '';
  if (honeypot.trim().length > 0) {
    return NextResponse.json({ ok: true });
  }

  const ip = clientIp(request);
  if (!withinRateLimit(ip)) {
    return NextResponse.json({ error: 'rate_limited' }, { status: 429 });
  }

  const payload: InquiryInput = {
    name: clean(body.name, MAX_FIELD),
    company: clean(body.company, MAX_FIELD),
    email: clean(body.email, MAX_FIELD),
    check_size: clean(body.check_size, MAX_FIELD),
    region: clean(body.region, MAX_FIELD),
    message: clean(body.message, MAX_MESSAGE),
    locale: clean(body.locale, 5) || 'en',
    ip,
    user_agent: (request.headers.get('user-agent') ?? '').slice(0, MAX_FIELD),
  };

  if (
    !payload.name ||
    !payload.company ||
    !payload.email ||
    !payload.message ||
    !EMAIL_RE.test(payload.email)
  ) {
    return NextResponse.json({ error: 'validation' }, { status: 400 });
  }

  let saved;
  try {
    saved = await addInquiry(payload);
  } catch (err) {
    console.error('[investors] failed to persist inquiry', err);
    return NextResponse.json({ error: 'storage' }, { status: 500 });
  }

  const notifyTo =
    process.env.INVESTOR_INQUIRY_TO ?? 'investors@bettingwithai.app';
  const subject = `Investor inquiry · ${saved.company || saved.name}`;
  const text = [
    `New investor inquiry`,
    ``,
    `Name: ${saved.name}`,
    `Company: ${saved.company}`,
    `Email: ${saved.email}`,
    `Check size / focus: ${saved.check_size || '-'}`,
    `Region: ${saved.region || '-'}`,
    `Locale: ${saved.locale}`,
    `IP: ${saved.ip}`,
    ``,
    `Message:`,
    saved.message,
    ``,
    `--`,
    `ID: ${saved.id}`,
    `Received: ${saved.created_at}`,
  ].join('\n');

  const mailRes = await sendMail({
    to: notifyTo,
    subject,
    text,
    replyTo: saved.email,
  });
  if (!mailRes.ok) {
    console.warn('[investors] notify mail failed:', mailRes.error);
  }

  return NextResponse.json({ ok: true, id: saved.id });
}
