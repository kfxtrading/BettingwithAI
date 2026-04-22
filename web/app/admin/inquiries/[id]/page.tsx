import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';
import { AdminReplyForm } from '@/components/AdminReplyForm';
import { isAdminAuthenticated } from '@/lib/adminAuth';
import { getInquiry } from '@/lib/inquiries';

export const dynamic = 'force-dynamic';

type PageProps = { params: { id: string } };

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

export default async function AdminInquiryDetailPage({ params }: PageProps) {
  if (!isAdminAuthenticated()) {
    redirect(`/admin/login?next=/admin/inquiries/${params.id}`);
  }

  const inquiry = await getInquiry(params.id);
  if (!inquiry) notFound();

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <Link
          href="/admin/inquiries"
          className="focus-ring text-2xs uppercase tracking-[0.08em] text-muted hover:text-text"
        >
          ← All inquiries
        </Link>
        <h1 className="mt-2 text-xl font-medium tracking-tight">
          {inquiry.name}
          <span className="text-muted"> · {inquiry.company}</span>
        </h1>
        <p className="mt-1 text-2xs uppercase tracking-[0.08em] text-muted">
          {formatDate(inquiry.created_at)} · status: {inquiry.status}
        </p>
      </div>

      <section className="surface-card flex flex-col gap-3 px-5 py-4">
        <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">
              Email
            </dt>
            <dd>
              <a
                href={`mailto:${inquiry.email}`}
                className="underline hover:text-text"
              >
                {inquiry.email}
              </a>
            </dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">
              Check size / focus
            </dt>
            <dd>{inquiry.check_size || '—'}</dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">
              Region
            </dt>
            <dd>{inquiry.region || '—'}</dd>
          </div>
          <div>
            <dt className="text-2xs uppercase tracking-[0.08em] text-muted">
              Locale
            </dt>
            <dd>{inquiry.locale}</dd>
          </div>
        </dl>
        <div>
          <h2 className="text-2xs uppercase tracking-[0.08em] text-muted">
            Message
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-text">
            {inquiry.message}
          </p>
        </div>
      </section>

      {inquiry.replies.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium">Replies sent</h2>
          <ul className="flex flex-col gap-3">
            {inquiry.replies.map((r, idx) => (
              <li
                key={`${r.at}-${idx}`}
                className="surface-card flex flex-col gap-2 px-5 py-4"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium">{r.subject}</span>
                  <span className="text-2xs text-muted">
                    {formatDate(r.at)}
                  </span>
                </div>
                <p className="whitespace-pre-wrap text-sm text-text">
                  {r.body}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">Reply</h2>
        <AdminReplyForm
          inquiryId={inquiry.id}
          to={inquiry.email}
          defaultSubject={`Re: Investor inquiry (${inquiry.company || inquiry.name})`}
          initialStatus={inquiry.status}
        />
      </section>
    </div>
  );
}
