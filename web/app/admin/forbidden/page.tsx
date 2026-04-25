import type { Metadata } from 'next';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Access denied',
  robots: { index: false, follow: false },
};

export default function AdminForbiddenPage() {
  return (
    <div className="mx-auto max-w-md text-center">
      <h1 className="text-xl font-medium tracking-tight">Access denied</h1>
      <p className="mt-2 text-sm text-muted">
        This area is restricted. If you reached this page, your identity was
        not recognised by the upstream Zero-Trust gateway.
      </p>
      <p className="mt-4 text-2xs uppercase tracking-[0.08em] text-muted">
        <a className="underline hover:text-text" href="/cdn-cgi/access/logout">
          Sign out of Cloudflare Access
        </a>
      </p>
    </div>
  );
}
