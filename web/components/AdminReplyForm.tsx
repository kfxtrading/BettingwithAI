'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import type { InquiryStatus } from '@/lib/inquiries';

type Props = {
  inquiryId: string;
  to: string;
  defaultSubject: string;
  initialStatus: InquiryStatus;
};

type Status = 'idle' | 'sending' | 'sent' | 'error';

export function AdminReplyForm({
  inquiryId,
  to,
  defaultSubject,
  initialStatus,
}: Props) {
  const router = useRouter();
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);

  async function onReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === 'sending') return;
    if (!subject.trim() || !body.trim()) {
      setStatus('error');
      setError('Subject and message are required.');
      return;
    }
    setStatus('sending');
    setError(null);
    try {
      const res = await fetch(`/api/admin/inquiries/${inquiryId}/reply`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ subject, body }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          error?: string;
        };
        throw new Error(data.error ?? `status ${res.status}`);
      }
      setStatus('sent');
      setBody('');
      router.refresh();
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'unknown');
    }
  }

  async function onUpdateStatus(nextStatus: InquiryStatus) {
    try {
      const res = await fetch(`/api/admin/inquiries/${inquiryId}/status`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'unknown');
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={onReply} className="flex flex-col gap-3">
        <p className="text-2xs uppercase tracking-[0.08em] text-muted">
          To: <span className="text-text">{to}</span>
        </p>
        <label htmlFor="reply-subject" className="flex flex-col gap-1.5">
          <span className="text-2xs uppercase tracking-[0.08em] text-muted">
            Subject
          </span>
          <input
            id="reply-subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="focus-ring rounded-[10px] border border-white/10 bg-surface px-3 py-2 text-sm text-text"
            required
          />
        </label>
        <label htmlFor="reply-body" className="flex flex-col gap-1.5">
          <span className="text-2xs uppercase tracking-[0.08em] text-muted">
            Message
          </span>
          <textarea
            id="reply-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={8}
            maxLength={5000}
            className="focus-ring rounded-[10px] border border-white/10 bg-surface px-3 py-2 text-sm text-text"
            required
          />
        </label>

        {status === 'error' && error && (
          <p role="alert" className="text-sm text-red-400">
            {error}
          </p>
        )}
        {status === 'sent' && (
          <p role="status" className="text-sm text-green-400">
            Reply sent.
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={status === 'sending'}
            className="focus-ring press inline-flex items-center rounded-full bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-60"
          >
            {status === 'sending' ? 'Sending...' : 'Send reply'}
          </button>
          <button
            type="button"
            onClick={() =>
              onUpdateStatus(initialStatus === 'archived' ? 'new' : 'archived')
            }
            className="focus-ring press rounded-full border border-white/15 px-3 py-1.5 text-xs text-muted hover:text-text"
          >
            {initialStatus === 'archived' ? 'Unarchive' : 'Archive'}
          </button>
        </div>
      </form>
    </div>
  );
}
