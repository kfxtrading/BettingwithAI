'use client';

import { useState, type FormEvent } from 'react';
import { useLocale } from '@/lib/i18n/LocaleProvider';

type Status = 'idle' | 'submitting' | 'sent' | 'error';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function InvestorInquiryForm() {
  const { t, locale } = useLocale();
  const [status, setStatus] = useState<Status>('idle');
  const [errorKey, setErrorKey] = useState<
    'page.investors.form.error.generic' | 'page.investors.form.error.validation' | null
  >(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === 'submitting') return;

    const form = event.currentTarget;
    const data = new FormData(form);
    const payload = {
      name: String(data.get('name') ?? '').trim(),
      company: String(data.get('company') ?? '').trim(),
      email: String(data.get('email') ?? '').trim(),
      check_size: String(data.get('check_size') ?? '').trim(),
      region: String(data.get('region') ?? '').trim(),
      message: String(data.get('message') ?? '').trim(),
      website: String(data.get('website') ?? ''),
      locale,
    };

    if (
      !payload.name ||
      !payload.company ||
      !payload.email ||
      !payload.message ||
      !EMAIL_RE.test(payload.email)
    ) {
      setStatus('error');
      setErrorKey('page.investors.form.error.validation');
      return;
    }

    setStatus('submitting');
    setErrorKey(null);

    try {
      const res = await fetch('/api/investors', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      setStatus('sent');
      form.reset();
    } catch {
      setStatus('error');
      setErrorKey('page.investors.form.error.generic');
    }
  }

  if (status === 'sent') {
    return (
      <div
        role="status"
        aria-live="polite"
        className="surface-card border-l-2 border-accent px-5 py-5"
      >
        <p className="text-sm font-medium text-text">
          {t('page.investors.form.success.title')}
        </p>
        <p className="mt-2 text-sm text-muted">
          {t('page.investors.form.success.body')}
        </p>
      </div>
    );
  }

  const submitting = status === 'submitting';

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
      <div
        aria-hidden="true"
        className="absolute -left-[9999px] top-auto h-px w-px overflow-hidden"
      >
        <label htmlFor="inv-website">Website</label>
        <input
          id="inv-website"
          type="text"
          name="website"
          tabIndex={-1}
          autoComplete="off"
        />
      </div>

      <Field
        id="inv-name"
        name="name"
        required
        autoComplete="name"
        label={t('page.investors.form.name')}
      />
      <Field
        id="inv-company"
        name="company"
        required
        autoComplete="organization"
        label={t('page.investors.form.company')}
      />
      <Field
        id="inv-email"
        name="email"
        type="email"
        required
        autoComplete="email"
        label={t('page.investors.form.email')}
      />
      <Field
        id="inv-check"
        name="check_size"
        label={t('page.investors.form.checkSize')}
      />
      <Field
        id="inv-region"
        name="region"
        label={t('page.investors.form.region')}
      />

      <label htmlFor="inv-message" className="flex flex-col gap-1.5">
        <span className="text-2xs uppercase tracking-[0.08em] text-muted">
          {t('page.investors.form.message')}
        </span>
        <textarea
          id="inv-message"
          name="message"
          required
          rows={5}
          maxLength={2000}
          className="focus-ring rounded-[10px] border border-white/10 bg-surface px-3 py-2 text-sm text-text placeholder:text-muted"
        />
      </label>

      {status === 'error' && errorKey && (
        <p role="alert" className="text-sm text-red-400">
          {t(errorKey)}
        </p>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="focus-ring press inline-flex items-center rounded-full bg-accent px-4 py-2 text-sm font-medium text-bg transition-opacity disabled:opacity-60"
        >
          {submitting
            ? t('page.investors.form.submitting')
            : t('page.investors.form.submit')}
        </button>
      </div>
    </form>
  );
}

type FieldProps = {
  id: string;
  name: string;
  label: string;
  type?: string;
  required?: boolean;
  autoComplete?: string;
};

function Field({ id, name, label, type = 'text', required, autoComplete }: FieldProps) {
  return (
    <label htmlFor={id} className="flex flex-col gap-1.5">
      <span className="text-2xs uppercase tracking-[0.08em] text-muted">
        {label}
        {required ? <span aria-hidden className="ml-1 text-accent">*</span> : null}
      </span>
      <input
        id={id}
        name={name}
        type={type}
        required={required}
        autoComplete={autoComplete}
        maxLength={300}
        className="focus-ring rounded-[10px] border border-white/10 bg-surface px-3 py-2 text-sm text-text placeholder:text-muted"
      />
    </label>
  );
}
