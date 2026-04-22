'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';

type Props = { next?: string; errored?: boolean };

export function AdminLoginForm({ next, errored }: Props) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'error'>(
    errored ? 'error' : 'idle',
  );

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === 'submitting') return;
    setStatus('submitting');
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) {
        setStatus('error');
        return;
      }
      router.replace(next ?? '/admin/inquiries');
      router.refresh();
    } catch {
      setStatus('error');
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <label htmlFor="admin-pw" className="flex flex-col gap-1.5">
        <span className="text-2xs uppercase tracking-[0.08em] text-muted">
          Password
        </span>
        <input
          id="admin-pw"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="focus-ring rounded-[10px] border border-white/10 bg-surface px-3 py-2 text-sm text-text"
        />
      </label>
      {status === 'error' && (
        <p role="alert" className="text-sm text-red-400">
          Incorrect password.
        </p>
      )}
      <button
        type="submit"
        disabled={status === 'submitting'}
        className="focus-ring press inline-flex items-center justify-center rounded-full bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-60"
      >
        {status === 'submitting' ? 'Signing in...' : 'Sign in'}
      </button>
    </form>
  );
}
