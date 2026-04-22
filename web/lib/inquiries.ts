import { promises as fs } from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';

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

const DEFAULT_STORE =
  process.env.INVESTOR_INQUIRY_STORE ??
  path.join(process.cwd(), 'data', 'investor-inquiries.json');

async function readAll(storePath: string): Promise<Inquiry[]> {
  try {
    const raw = await fs.readFile(storePath, 'utf8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Inquiry[]) : [];
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return [];
    throw err;
  }
}

async function writeAll(storePath: string, items: Inquiry[]): Promise<void> {
  await fs.mkdir(path.dirname(storePath), { recursive: true });
  const tmp = `${storePath}.tmp`;
  await fs.writeFile(tmp, JSON.stringify(items, null, 2), 'utf8');
  await fs.rename(tmp, storePath);
}

export async function listInquiries(): Promise<Inquiry[]> {
  const items = await readAll(DEFAULT_STORE);
  return items.sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
}

export async function getInquiry(id: string): Promise<Inquiry | null> {
  const items = await readAll(DEFAULT_STORE);
  return items.find((x) => x.id === id) ?? null;
}

export async function addInquiry(input: InquiryInput): Promise<Inquiry> {
  const items = await readAll(DEFAULT_STORE);
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
  items.push(entry);
  await writeAll(DEFAULT_STORE, items);
  return entry;
}

export async function updateInquiryStatus(
  id: string,
  status: InquiryStatus,
): Promise<Inquiry | null> {
  const items = await readAll(DEFAULT_STORE);
  const idx = items.findIndex((x) => x.id === id);
  if (idx < 0) return null;
  items[idx] = { ...items[idx], status };
  await writeAll(DEFAULT_STORE, items);
  return items[idx];
}

export async function appendReply(
  id: string,
  reply: Omit<InquiryReply, 'at'>,
): Promise<Inquiry | null> {
  const items = await readAll(DEFAULT_STORE);
  const idx = items.findIndex((x) => x.id === id);
  if (idx < 0) return null;
  const full: InquiryReply = { ...reply, at: new Date().toISOString() };
  items[idx] = {
    ...items[idx],
    status: 'replied',
    replies: [...items[idx].replies, full],
  };
  await writeAll(DEFAULT_STORE, items);
  return items[idx];
}
