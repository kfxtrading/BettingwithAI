'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { KpiTile } from '@/components/KpiTile';
import { PerformanceIndexChart } from '@/components/PerformanceIndexChart';
import { RuleAccordion } from '@/components/RuleAccordion';
import { Section } from '@/components/Section';
import { api, queryKeys } from '@/lib/api';

const STALE_THRESHOLD_HOURS = 48;

function formatTrackingStart(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat('de-DE', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(d);
  } catch {
    return iso;
  }
}

function hoursSince(iso: string): number {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return 0;
  return (Date.now() - d.getTime()) / 3_600_000;
}

function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function PerformanceTracker() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.performanceIndex,
    queryFn: api.performanceIndex,
    staleTime: 5 * 60_000,
  });

  const caption = data
    ? `seit ${formatTrackingStart(data.tracking_started_at)}`
    : 'Transparenter Verlauf der Modell-Performance';

  const tone = (v: number): 'positive' | 'negative' | 'default' =>
    v > 100 ? 'positive' : v < 100 ? 'negative' : 'default';

  const stale =
    data != null && hoursSince(data.updated_at) > STALE_THRESHOLD_HOURS;

  return (
    <Section title="Transparenz-Tracker" caption={caption}>
      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="h-24 animate-pulse rounded-[14px] bg-surface-2"
              />
            ))}
          </div>
          <div className="h-80 animate-pulse rounded-[14px] bg-surface-2" />
        </div>
      ) : isError || !data ? (
        <div className="surface-card px-5 py-12 text-center text-sm text-muted">
          Performance-Daten werden aktualisiert.
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <KpiTile
              label="Index"
              value={data.current_index.toFixed(2)}
              tone={tone(data.current_index)}
              hint={
                data.all_time_high_index > data.current_index
                  ? `ATH ${data.all_time_high_index.toFixed(2)}`
                  : 'Auf Allzeithoch'
              }
            />
            <KpiTile
              label="Trefferquote"
              value={data.hit_rate != null ? pct(data.hit_rate) : '—'}
              hint={
                data.hit_rate == null
                  ? 'Noch keine Wette abgeschlossen'
                  : 'Wins / gewertete Bets'
              }
            />
            <KpiTile
              label="Spiele"
              value={data.n_bets}
              hint={`${data.n_days_tracked} Tage getrackt`}
            />
          </div>

          <PerformanceIndexChart data={data.equity_curve} />

          <div className="flex flex-col gap-2 text-sm text-muted md:flex-row md:items-center md:justify-between">
            <span>
              Max. Drawdown:{' '}
              <span className="font-mono text-negative">
                -{pct(data.max_drawdown_pct)}
              </span>
              {data.current_drawdown_pct > 0 && (
                <>
                  {'  ·  '}aktuell{' '}
                  <span className="font-mono">
                    -{pct(data.current_drawdown_pct)}
                  </span>
                </>
              )}
            </span>
            <span className="text-2xs uppercase tracking-[0.08em]">
              Modell v{data.model_version} · {data.rule_hash.slice(0, 18)}…
            </span>
          </div>

          {stale && (
            <p className="text-2xs text-muted">
              Daten werden aktualisiert (letzter Stand{' '}
              {formatTrackingStart(data.updated_at)}).
            </p>
          )}

          <RuleAccordion />

          <p className="text-2xs leading-relaxed text-muted">
            Hypothetische Simulation eines statistischen Modells auf Basis
            vergangener Spieldaten. Keine Aufforderung zum Glücksspiel.
            Keine Gewähr auf zukünftige Ergebnisse. Glücksspiele bergen
            finanzielle Risiken. Hilfe unter
            www.bundesweite-suchtberatung.de oder Tel. 0800 1 372 700. Nur
            für Personen ab 18 Jahren.
          </p>

          <div className="flex justify-center pt-2">
            <Link
              href="/performance"
              className="focus-ring press inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-sm font-medium text-white"
            >
              Volle Details ansehen
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      )}
    </Section>
  );
}
