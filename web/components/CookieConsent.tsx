'use client';

import { useEffect, useState } from 'react';
import { api, type ConsentCategory, type ConsentPayload } from '@/lib/api';

const STORAGE_KEY = 'bwai.cookie-consent.v1';
const CONSENT_VERSION = '1.0';

type StoredConsent = {
  accepted: boolean;
  categories: ConsentCategory[];
  version: string;
  savedAt: string;
};

function readStored(): StoredConsent | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredConsent;
    if (parsed.version !== CONSENT_VERSION) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStored(value: StoredConsent): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    /* ignore quota / privacy errors */
  }
}

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [analytics, setAnalytics] = useState(true);
  const [marketing, setMarketing] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const stored = readStored();
    if (stored) return;
    let cancelled = false;
    api
      .getConsent()
      .then((remote) => {
        if (cancelled) return;
        if (remote && remote.version === CONSENT_VERSION) {
          writeStored({
            accepted: remote.accepted,
            categories: remote.categories,
            version: remote.version,
            savedAt: remote.updated_at,
          });
          return;
        }
        setVisible(true);
      })
      .catch(() => {
        if (!cancelled) setVisible(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const persist = async (payload: ConsentPayload): Promise<void> => {
    setSubmitting(true);
    const fallback: StoredConsent = {
      accepted: payload.accepted,
      categories: payload.categories,
      version: CONSENT_VERSION,
      savedAt: new Date().toISOString(),
    };
    writeStored(fallback);
    try {
      const saved = await api.saveConsent({ ...payload, version: CONSENT_VERSION });
      writeStored({
        accepted: saved.accepted,
        categories: saved.categories,
        version: saved.version,
        savedAt: saved.updated_at,
      });
    } catch {
      /* keep local fallback if backend is unreachable */
    } finally {
      setSubmitting(false);
      setVisible(false);
    }
  };

  const acceptAll = (): Promise<void> =>
    persist({
      accepted: true,
      categories: ['necessary', 'analytics', 'marketing'],
    });

  const rejectAll = (): Promise<void> =>
    persist({ accepted: false, categories: ['necessary'] });

  const saveSelection = (): Promise<void> => {
    const categories: ConsentCategory[] = ['necessary'];
    if (analytics) categories.push('analytics');
    if (marketing) categories.push('marketing');
    return persist({ accepted: analytics || marketing, categories });
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-live="polite"
      aria-label="Cookie-Einwilligung"
      className="fixed inset-x-0 bottom-0 z-50 px-4 pb-4 md:px-6 md:pb-6"
    >
      <div className="mx-auto w-full max-w-3xl rounded-2xl border border-white/10 bg-surface/95 p-5 text-sm shadow-soft backdrop-blur md:p-6">
        <h2 className="text-base font-medium text-text">
          Wir nutzen Cookies
        </h2>
        <p className="mt-2 text-muted">
          Diese Website verwendet Cookies und vergleichbare Technologien, um
          die Funktion sicherzustellen sowie Reichweite und Performance zu
          analysieren. Deine Einwilligung wird zusammen mit einem Hash deiner
          IP-Adresse gespeichert, damit wir sie bei deinem nächsten Besuch
          erneut erkennen. Du kannst sie jederzeit widerrufen.
        </p>

        {showDetails && (
          <div className="mt-4 space-y-2 rounded-xl border border-white/10 bg-bg/50 p-3">
            <label className="flex items-start gap-3 opacity-80">
              <input
                type="checkbox"
                checked
                disabled
                className="mt-1 h-4 w-4 accent-accent"
              />
              <span>
                <span className="block font-medium text-text">
                  Notwendig
                </span>
                <span className="text-xs text-muted">
                  Erforderlich für den Betrieb der Seite. Immer aktiv.
                </span>
              </span>
            </label>
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={analytics}
                onChange={(e) => setAnalytics(e.target.checked)}
                className="mt-1 h-4 w-4 accent-accent"
              />
              <span>
                <span className="block font-medium text-text">
                  Statistik
                </span>
                <span className="text-xs text-muted">
                  Anonyme Nutzungsmessung zur Verbesserung der Seite.
                </span>
              </span>
            </label>
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={marketing}
                onChange={(e) => setMarketing(e.target.checked)}
                className="mt-1 h-4 w-4 accent-accent"
              />
              <span>
                <span className="block font-medium text-text">
                  Marketing
                </span>
                <span className="text-xs text-muted">
                  Personalisierte Inhalte und Drittanbieter-Tracking.
                </span>
              </span>
            </label>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => setShowDetails((v) => !v)}
            className="focus-ring rounded-full px-3.5 py-1.5 text-xs text-muted hover:text-text"
          >
            {showDetails ? 'Details ausblenden' : 'Einstellungen'}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={rejectAll}
            className="focus-ring press rounded-full border border-white/10 px-4 py-1.5 text-text hover:bg-white/5 disabled:opacity-50"
          >
            Ablehnen
          </button>
          {showDetails && (
            <button
              type="button"
              disabled={submitting}
              onClick={saveSelection}
              className="focus-ring press rounded-full border border-white/10 px-4 py-1.5 text-text hover:bg-white/5 disabled:opacity-50"
            >
              Auswahl speichern
            </button>
          )}
          <button
            type="button"
            disabled={submitting}
            onClick={acceptAll}
            className="focus-ring press rounded-full bg-accent px-4 py-1.5 font-medium text-bg disabled:opacity-50"
          >
            Alle akzeptieren
          </button>
        </div>
      </div>
    </div>
  );
}
