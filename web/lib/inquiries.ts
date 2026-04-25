import { promises as fs } from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { kv } from '@vercel/kv';

export type InquiryStatus = 'new' | 'replied' | 'archived';

export type InquiryReply = {
  at: string;
  subject: string;
  body: string;
};

export type Inquiry = {
  id: string;
  created_at: string;
  name: string;
  company: string;
  email: string;
  check_size: string;
  region: string;
  message: string;
  locale: string;
  ip: string;
  user_agent: string;
  status: InquiryStatus;
  replies: InquiryReply[];
};

export type InquiryInput = {
  name: string;
  company: string;
  email: string;
  check_size?: string;
  region?: string;
  message: string;
  locale?: string;
  ip?: string;
  user_agent?: string;
};

// KV is used in production (Vercel injects KV_REST_API_*). Local dev without
// those env vars falls back to a JSON file so `npm run dev` works offline.
function useKv(): boolean {
  return !!process.env.KV_REST_API_URL && !!process.env.KV_REST_API_TOKEN;
}

const INDEX_KEY = 'inquiries:index';
const itemKey = (id: string) => `inquiries:item:${id}`;

async function kvList(): Promise<Inquiry[]> {
  const ids = (await kv.zrange<string[]>(INDEX_KEY, 0, -1, { rev: true })) ?? [];
  if (ids.length === 0) return [];
  const items = await Promise.all(
    ids.map((id) => kv.get<Inquiry>(itemKey(id))),
  );
  return items.filter((x): x is Inquiry => x !== null);
}

async function kvGet(id: string): Promise<Inquiry | null> {
  const v = await kv.get<Inquiry>(itemKey(id));
  return v ?? null;
}

async function kvAdd(entry: Inquiry): Promise<void> {
  const score = Date.parse(entry.created_at);
  await kv.set(itemKey(entry.id), entry);
  await kv.zadd(INDEX_KEY, { score, member: entry.id });
}

async function kvPut(entry: Inquiry): Promise<void> {
  await kv.set(itemKey(entry.id), entry);
}

const FILE_STORE =
  process.env.INVESTOR_INQUIRY_STORE ??
  path.join(process.cwd(), 'data', 'investor-inquiries.json');

async function fileReadAll(): Promise<Inquiry[]> {
  try {
    const raw = await fs.readFile(FILE_STORE, 'utf8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Inquiry[]) : [];
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return [];
    throw err;
  }
}

async function fileWriteAll(items: Inquiry[]): Promise<void> {
  await fs.mkdir(path.dirname(FILE_STORE), { recursive: true });
  const tmp = `${FILE_STORE}.tmp`;
  await fs.writeFile(tmp, JSON.stringify(items, null, 2), 'utf8');
  await fs.rename(tmp, FILE_STORE);
}

export async function listInquiries(): Promise<Inquiry[]> {
  if (useKv()) return kvList();
  const items = await fileReadAll();
  return items.sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
}

export async function getInquiry(id: string): Promise<Inquiry | null> {
  if (useKv()) return kvGet(id);
  const items = await fileReadAll();
  return items.find((x) => x.id === id) ?? null;
}

export async function addInquiry(input: InquiryInput): Promise<Inquiry> {
  const entry: Inquiry = {
    id: randomUUID(),
    created_at: new Date().toISOString(),
    name: input.name,
    company: input.company,
    email: input.email,
    check_size: input.check_size ?? '',
    region: input.region ?? '',
    message: input.message,
    locale: input.locale ?? 'en',
    ip: input.ip ?? '',
    user_agent: input.user_agent ?? '',
    status: 'new',
    replies: [],
  };
  if (useKv()) {
    await kvAdd(entry);
  } else {
    const items = await fileReadAll();
    items.push(entry);
    await fileWriteAll(items);
  }
  return entry;
}

export async function updateInquiryStatus(
  id: string,
  status: InquiryStatus,
): Promise<Inquiry | null> {
  if (useKv()) {
    const existing = await kvGet(id);
    if (!existing) return null;
    const updated: Inquiry = { ...existing, status };
    await kvPut(updated);
    return updated;
  }
  const items = await fileReadAll();
  const idx = items.findIndex((x) => x.id === id);
  if (idx < 0) return null;
  items[idx] = { ...items[idx], status };
  await fileWriteAll(items);
  return items[idx];
}

export async function appendReply(
  id: string,
  reply: Omit<InquiryReply, 'at'>,
): Promise<Inquiry | null> {
  const full: InquiryReply = { ...reply, at: new Date().toISOString() };
  if (useKv()) {
    const existing = await kvGet(id);
    if (!existing) return null;
    const updated: Inquiry = {
      ...existing,
      status: 'replied',
      replies: [...existing.replies, full],
    };
    await kvPut(updated);
    return updated;
  }
  const items = await fileReadAll();
  const idx = items.findIndex((x) => x.id === id);
  if (idx < 0) return null;
  items[idx] = {
    ...items[idx],
    status: 'replied',
    replies: [...items[idx].replies, full],
  };
  await fileWriteAll(items);
  return items[idx];
}
