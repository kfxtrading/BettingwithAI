/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';
const isBuildPhase = process.env.NEXT_PHASE === 'phase-production-build';

if (isProd && isBuildPhase) {
  const missing = [];
  if (!process.env.NEXT_PUBLIC_API_URL) missing.push('NEXT_PUBLIC_API_URL');
  if (!process.env.NEXT_PUBLIC_SITE_URL) missing.push('NEXT_PUBLIC_SITE_URL');
  if (missing.length) {
    throw new Error(
      `[next.config] Missing required production env vars: ${missing.join(', ')}. ` +
        `Browser bundles would fall back to localhost and the UI would stay in a loading state.`,
    );
  }
}

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
    NEXT_PUBLIC_SITE_URL:
      process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000',
  },
};

export default nextConfig;
