'use client';

import { useEffect, useState } from 'react';
import { useLocale } from '@/lib/i18n/LocaleProvider';

const CONSENT_STORAGE_KEY = 'bwai.cookie-consent.v1';
const CONSENT_VERSION = '1.0';
const PER_WIDGET_OVERRIDE_KEY = 'bwai.sofascore.lineups.optin.v1';

const WIDGET_BASE_URL = 'https://widget.sofascore.com/';

type StoredConsent = {
  accepted: boolean;
  categories: string[];
  version: string;
  savedAt: string;
};

function hasMarketingConsent(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const raw = window.localStorage.getItem(CONSENT_STORAGE_KEY);
    if (!raw) return false;
    const parsed = JSON.parse(raw) as StoredConsent;
    if (parsed.version !== CONSENT_VERSION) return false;
    return parsed.categories.includes('marketing');
  } catch {
    return false;
  }
}

function hasPerWidgetOverride(eventId: number): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const raw = window.sessionStorage.getItem(PER_WIDGET_OVERRIDE_KEY);
    if (!raw) return false;
    const ids = JSON.parse(raw) as number[];
    return Array.isArray(ids) && ids.includes(eventId);
  } catch {
    return false;
  }
}

function persistPerWidgetOverride(eventId: number): void {
  try {
    const raw = window.sessionStorage.getItem(PER_WIDGET_OVERRIDE_KEY);
    const ids: number[] = raw ? (JSON.parse(raw) as number[]) : [];
    if (!ids.includes(eventId)) ids.push(eventId);
    window.sessionStorage.setItem(
      PER_WIDGET_OVERRIDE_KEY,
      JSON.stringify(ids),
    );
  } catch {
    /* ignore quota / privacy errors */
  }
}

type Props = {
  eventId: number;
  homeTeam: string;
  awayTeam: string;
};

export function SofascoreLineupsWidget({
  eventId,
  homeTeam,
  awayTeam,
}: Props) {
  const { t } = useLocale();
  const [allowed, setAllowed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
    setAllowed(hasMarketingConsent() || hasPerWidgetOverride(eventId));
  }, [eventId]);

  if (!hydrated) {
    return (
      <div
        aria-hidden="true"
        className="surface-card flex h-[760px] w-full items-center justify-center px-4 py-3"
      />
    );
  }

  if (!allowed) {
    return (
      <div className="surface-card px-4 py-6">
        <p className="text-sm text-text">
          {t('match.lineups.consentPrompt')}
        </p>
        <p className="mt-2 text-2xs uppercase tracking-[0.08em] text-muted">
          {t('match.lineups.consentNote')}
        </p>
        <button
          type="button"
          onClick={() => {
            persistPerWidgetOverride(eventId);
            setAllowed(true);
          }}
          className="focus-ring mt-4 inline-flex items-center justify-center rounded-md border border-white/10 bg-white/5 px-4 py-2 text-2xs font-medium uppercase tracking-[0.08em] text-text transition hover:bg-white/10"
        >
          {t('match.lineups.consentButton')}
        </button>
      </div>
    );
  }

  const src = `${WIDGET_BASE_URL}?id=${eventId}&widgetTitle=lineups&type=lineups`;
  return (
    <iframe
      src={src}
      title={`Sofascore lineups: ${homeTeam} vs ${awayTeam}`}
      loading="lazy"
      sandbox="allow-scripts allow-same-origin allow-popups"
      referrerPolicy="no-referrer-when-downgrade"
      className="h-[760px] w-full rounded-md border border-white/10 bg-bg"
    />
  );
}
