import Link from 'next/link';
import { redirect } from 'next/navigation';
import { isAdminAuthenticated } from '@/lib/adminAuth';
import { listInquiries, type Inquiry } from '@/lib/inquiries';

export const dynamic = 'force-dynamic';

function statusBadge(status: Inquiry['status']) {
  const tone =
    status === 'new'
      ? 'bg-accent/20 text-accent'
      : status === 'replied'
        ? 'bg-green-500/15 text-green-300'
        : 'bg-white/10 text-muted';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-2xs uppercase tracking-[0.08em] ${tone}`}
    >
      {status}
    </span>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-GB', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default async function AdminInquiriesPage() {
  if (!isAdminAuthenticated()) {
    redirect('/admin/login?next=/admin/inquiries');
  }

  const inquiries = await listInquiries();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-baseline justify-between gap-3">
        <h1 className="text-xl font-medium tracking-tight">
          Investor inquiries
        </h1>
        <span className="text-2xs uppercase tracking-[0.08em] text-muted">
          {inquiries.length} total
        </span>
      </div>

      {inquiries.length === 0 ? (
        <div className="surface-card px-5 py-8 text-sm text-muted">
          No inquiries yet.
        </div>
      ) : (
        <ul className="flex flex-col divide-y divide-white/5 rounded-[14px] border border-white/10 bg-surface">
          {inquiries.map((i) => (
            <li key={i.id}>
              <Link
                href={`/admin/inquiries/${i.id}`}
                className="focus-ring flex flex-col gap-1 px-5 py-4 transition-colors hover:bg-white/5"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-text">
                    {i.name}
                  </span>
                  <span className="text-xs text-muted">· {i.company}</span>
                  <span className="ml-auto flex items-center gap-2">
                    {statusBadge(i.status)}
                    <span className="text-2xs text-muted">
                      {formatDate(i.created_at)}
                    </span>
                  </span>
                </div>
                <p className="line-clamp-2 text-xs text-muted">{i.message}</p>
                <p className="text-2xs text-muted/80">
                  {i.email}
                  {i.region ? ` · ${i.region}` : ''}
                  {i.check_size ? ` · ${i.check_size}` : ''}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
