import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Admin · Betting with AI',
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh bg-bg text-text">
      <header className="border-b border-white/10">
        <div className="mx-auto flex w-full max-w-page items-center justify-between px-6 py-4 md:px-12">
          <Link
            href="/admin/inquiries"
            className="focus-ring flex items-baseline gap-2 text-sm font-medium tracking-tight"
          >
            <span className="inline-block h-2 w-2 rounded-full bg-accent" />
            Betting with AI · Admin
          </Link>
          <form action="/api/admin/logout" method="post">
            <button
              type="submit"
              className="focus-ring press rounded-full border border-white/15 px-3 py-1 text-xs text-muted hover:text-text"
            >
              Sign out
            </button>
          </form>
        </div>
      </header>
      <main className="mx-auto w-full max-w-page px-6 py-8 md:px-12">
        {children}
      </main>
    </div>
  );
}
