import { cookies, headers } from 'next/headers';
import { redirect } from 'next/navigation';
import type { NextRequest } from 'next/server';

export type AccessIdentity = { email: string };

const JWKS_TTL_MS = 60 * 60 * 1000;

type Jwk = {
  kid: string;
  kty: string;
  n: string;
  e: string;
  alg?: string;
  use?: string;
};

type JwksCache = { fetchedAt: number; keys: Map<string, CryptoKey> };

let jwksCache: JwksCache | null = null;

function teamDomain(): string {
  const v = process.env.CF_ACCESS_TEAM_DOMAIN ?? '';
  return v.replace(/^https?:\/\//, '').replace(/\/+$/, '');
}

function expectedAud(): string {
  return process.env.CF_ACCESS_AUD ?? '';
}

function ownerEmail(): string {
  return (process.env.OWNER_EMAIL ?? '').trim().toLowerCase();
}

function devOwnerAllowed(): boolean {
  return (
    process.env.NODE_ENV !== 'production' &&
    process.env.ALLOW_DEV_OWNER === '1'
  );
}

function base64UrlDecode(input: string): Uint8Array {
  const pad = input.length % 4 === 0 ? 0 : 4 - (input.length % 4);
  const b64 = input.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat(pad);
  const bin = Buffer.from(b64, 'base64');
  return new Uint8Array(bin);
}

function decodeJsonSegment<T = unknown>(seg: string): T {
  const bytes = base64UrlDecode(seg);
  return JSON.parse(new TextDecoder().decode(bytes)) as T;
}

async function fetchJwks(): Promise<Map<string, CryptoKey>> {
  const now = Date.now();
  if (jwksCache && now - jwksCache.fetchedAt < JWKS_TTL_MS) {
    return jwksCache.keys;
  }
  const team = teamDomain();
  if (!team) throw new Error('CF_ACCESS_TEAM_DOMAIN not set');
  const url = `https://${team}/cdn-cgi/access/certs`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`jwks_fetch_failed_${res.status}`);
  const body = (await res.json()) as { keys?: Jwk[] };
  const keys = new Map<string, CryptoKey>();
  for (const jwk of body.keys ?? []) {
    if (jwk.kty !== 'RSA') continue;
    const key = await crypto.subtle.importKey(
      'jwk',
      jwk as JsonWebKey,
      { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
      false,
      ['verify'],
    );
    keys.set(jwk.kid, key);
  }
  jwksCache = { fetchedAt: now, keys };
  return keys;
}

type JwtPayload = {
  aud?: string | string[];
  iss?: string;
  email?: string;
  exp?: number;
  nbf?: number;
};

async function verifyToken(token: string): Promise<JwtPayload | null> {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, sigB64] = parts;
  let header: { kid?: string; alg?: string };
  let payload: JwtPayload;
  try {
    header = decodeJsonSegment(headerB64);
    payload = decodeJsonSegment<JwtPayload>(payloadB64);
  } catch {
    return null;
  }
  if (header.alg !== 'RS256' || !header.kid) return null;

  let keys: Map<string, CryptoKey>;
  try {
    keys = await fetchJwks();
  } catch {
    return null;
  }
  const key = keys.get(header.kid);
  if (!key) return null;

  const dataView = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const sigView = base64UrlDecode(sigB64);
  const data = new Uint8Array(dataView).buffer;
  const signature = new Uint8Array(sigView).buffer;
  let valid = false;
  try {
    valid = await crypto.subtle.verify(
      { name: 'RSASSA-PKCS1-v1_5' },
      key,
      signature,
      data,
    );
  } catch {
    return null;
  }
  if (!valid) return null;

  const now = Math.floor(Date.now() / 1000);
  if (typeof payload.exp === 'number' && now >= payload.exp) return null;
  if (typeof payload.nbf === 'number' && now < payload.nbf) return null;

  const aud = expectedAud();
  if (aud) {
    const got = payload.aud;
    const ok = Array.isArray(got) ? got.includes(aud) : got === aud;
    if (!ok) return null;
  }

  const team = teamDomain();
  if (team && payload.iss && payload.iss !== `https://${team}`) return null;

  return payload;
}

function readTokenFromHeaders(
  get: (name: string) => string | null | undefined,
): string | null {
  const header = get('cf-access-jwt-assertion');
  if (header && header.length > 0) return header;
  const cookie = get('cookie') ?? '';
  const match = /(?:^|;\s*)CF_Authorization=([^;]+)/.exec(cookie);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function getAccessIdentity(): Promise<AccessIdentity | null> {
  const h = headers();
  if (devOwnerAllowed()) {
    const dev = h.get('x-dev-owner');
    if (dev) return { email: dev.trim().toLowerCase() };
  }
  const c = cookies();
  const cookieToken = c.get('CF_Authorization')?.value ?? null;
  const token =
    h.get('cf-access-jwt-assertion') ??
    cookieToken ??
    null;
  if (!token) return null;
  const payload = await verifyToken(token);
  if (!payload || !payload.email) return null;
  return { email: payload.email.toLowerCase() };
}

export async function getAccessIdentityReq(
  req: NextRequest,
): Promise<AccessIdentity | null> {
  if (devOwnerAllowed()) {
    const dev = req.headers.get('x-dev-owner');
    if (dev) return { email: dev.trim().toLowerCase() };
  }
  const token = readTokenFromHeaders((name) => {
    if (name === 'cookie') {
      const all: string[] = [];
      req.cookies.getAll().forEach((c) => {
        all.push(`${c.name}=${c.value}`);
      });
      return all.join('; ');
    }
    return req.headers.get(name);
  });
  if (!token) return null;
  const payload = await verifyToken(token);
  if (!payload || !payload.email) return null;
  return { email: payload.email.toLowerCase() };
}

export function isOwner(identity: AccessIdentity | null): boolean {
  if (!identity) return false;
  const owner = ownerEmail();
  if (!owner) return false;
  return identity.email === owner;
}

export async function requireOwner(): Promise<AccessIdentity> {
  const id = await getAccessIdentity();
  if (!isOwner(id)) {
    redirect('/admin/forbidden');
  }
  return id as AccessIdentity;
}

export async function requireOwnerReq(
  req: NextRequest,
): Promise<AccessIdentity | null> {
  const id = await getAccessIdentityReq(req);
  if (!isOwner(id)) return null;
  return id;
}
