'use client';

import { useMemo, useState } from 'react';

type OddsFormat = 'decimal' | 'american' | 'fractional';

function parseDecimalOdds(raw: string, format: OddsFormat): number | null {
  const s = raw.trim();
  if (!s) return null;
  if (format === 'decimal') {
    const v = Number(s);
    return Number.isFinite(v) && v > 1 ? v : null;
  }
  if (format === 'american') {
    const v = Number(s);
    if (!Number.isFinite(v) || v === 0) return null;
    return v > 0 ? 1 + v / 100 : 1 + 100 / Math.abs(v);
  }
  // fractional: "5/2"
  const m = s.match(/^\s*(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)\s*$/);
  if (!m) return null;
  const num = Number(m[1]);
  const den = Number(m[2]);
  if (!den || !Number.isFinite(num) || !Number.isFinite(den)) return null;
  return 1 + num / den;
}

function formatPct(v: number): string {
  return `${(v * 100).toFixed(2)}%`;
}

function formatMoney(v: number, currency: string): string {
  return `${currency}${v.toFixed(2)}`;
}

export function KellyCalculator() {
  const [format, setFormat] = useState<OddsFormat>('decimal');
  const [oddsRaw, setOddsRaw] = useState('2.10');
  const [probPctRaw, setProbPctRaw] = useState('55');
  const [bankrollRaw, setBankrollRaw] = useState('1000');
  const [fraction, setFraction] = useState(0.5);
  const [currency, setCurrency] = useState('£');

  const decimalOdds = parseDecimalOdds(oddsRaw, format);
  const p = useMemo(() => {
    const v = Number(probPctRaw);
    return Number.isFinite(v) ? v / 100 : NaN;
  }, [probPctRaw]);
  const bankroll = useMemo(() => {
    const v = Number(bankrollRaw);
    return Number.isFinite(v) && v > 0 ? v : NaN;
  }, [bankrollRaw]);

  const valid =
    decimalOdds !== null &&
    Number.isFinite(p) &&
    p >= 0 &&
    p <= 1 &&
    Number.isFinite(bankroll);

  const result = useMemo(() => {
    if (!valid || decimalOdds === null) return null;
    const b = decimalOdds - 1;
    const q = 1 - p;
    const fullKelly = (b * p - q) / b;
    const ev = p * decimalOdds - 1;
    const impliedProb = 1 / decimalOdds;
    const edge = p - impliedProb;
    const fractionalKelly = fullKelly * fraction;
    const stake = Math.max(0, fractionalKelly) * bankroll;
    const stakeFull = Math.max(0, fullKelly) * bankroll;
    return {
      fullKelly,
      fractionalKelly,
      stake,
      stakeFull,
      ev,
      impliedProb,
      edge,
      decimalOdds,
    };
  }, [valid, decimalOdds, p, bankroll, fraction]);

  const negative = result !== null && result.fullKelly <= 0;

  return (
    <div className="not-prose space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="block text-2xs uppercase tracking-[0.08em] text-muted">
            Odds format
          </span>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as OddsFormat)}
            className="focus-ring mt-2 w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-text"
          >
            <option value="decimal">Decimal (e.g. 2.10)</option>
            <option value="american">American (e.g. +110, -120)</option>
            <option value="fractional">Fractional (e.g. 11/10)</option>
          </select>
        </label>
        <label className="block">
          <span className="block text-2xs uppercase tracking-[0.08em] text-muted">
            Bookmaker odds
          </span>
          <input
            value={oddsRaw}
            onChange={(e) => setOddsRaw(e.target.value)}
            inputMode="decimal"
            className="focus-ring mt-2 w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-text"
            placeholder={
              format === 'decimal'
                ? '2.10'
                : format === 'american'
                  ? '+110'
                  : '11/10'
            }
          />
        </label>
        <label className="block">
          <span className="block text-2xs uppercase tracking-[0.08em] text-muted">
            Your win probability (%)
          </span>
          <input
            value={probPctRaw}
            onChange={(e) => setProbPctRaw(e.target.value)}
            inputMode="decimal"
            className="focus-ring mt-2 w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-text"
            placeholder="55"
          />
        </label>
        <label className="block">
          <span className="block text-2xs uppercase tracking-[0.08em] text-muted">
            Bankroll
          </span>
          <div className="mt-2 flex gap-2">
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="focus-ring rounded-md border border-white/10 bg-white/5 px-2 py-2 text-sm text-text"
              aria-label="Currency"
            >
              <option value="£">£</option>
              <option value="€">€</option>
              <option value="$">$</option>
            </select>
            <input
              value={bankrollRaw}
              onChange={(e) => setBankrollRaw(e.target.value)}
              inputMode="decimal"
              className="focus-ring w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-text"
              placeholder="1000"
            />
          </div>
        </label>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <span className="text-2xs uppercase tracking-[0.08em] text-muted">
            Kelly fraction
          </span>
          <span className="font-mono text-sm text-text">
            {(fraction * 100).toFixed(0)}% × full Kelly
          </span>
        </div>
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          value={fraction}
          onChange={(e) => setFraction(Number(e.target.value))}
          className="mt-2 w-full accent-accent"
          aria-label="Kelly fraction"
        />
        <div className="mt-1 flex justify-between text-2xs text-muted">
          <span>10% (very conservative)</span>
          <span>50% (half-Kelly)</span>
          <span>100% (full)</span>
        </div>
      </div>

      {!valid && (
        <p
          className="rounded-md border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-200"
          role="status"
        >
          Enter valid odds (&gt; 1.00 decimal), a probability between 0 and 100%,
          and a positive bankroll.
        </p>
      )}

      {result && (
        <div className="surface-card grid gap-4 px-5 py-5 sm:grid-cols-2">
          <Stat
            label="Implied probability (raw)"
            value={formatPct(result.impliedProb)}
            hint={`From decimal odds ${result.decimalOdds.toFixed(3)}`}
          />
          <Stat
            label="Your edge"
            value={formatPct(result.edge)}
            hint={result.edge > 0 ? 'Positive — value bet' : 'No edge or negative — do not bet'}
            tone={result.edge > 0 ? 'positive' : 'negative'}
          />
          <Stat
            label="Expected value (per £1 staked)"
            value={`${result.ev >= 0 ? '+' : ''}${formatPct(result.ev)}`}
            tone={result.ev > 0 ? 'positive' : 'negative'}
          />
          <Stat
            label="Full Kelly fraction f*"
            value={formatPct(result.fullKelly)}
            tone={negative ? 'negative' : 'positive'}
          />
          <Stat
            label={`Stake at ${(fraction * 100).toFixed(0)}% Kelly`}
            value={
              result.fractionalKelly > 0
                ? formatMoney(result.stake, currency)
                : formatMoney(0, currency)
            }
            hint={
              result.fractionalKelly > 0
                ? `${formatPct(result.fractionalKelly)} of bankroll`
                : 'Zero — Kelly says do not bet'
            }
            tone={result.fractionalKelly > 0 ? 'positive' : 'negative'}
          />
          <Stat
            label="Stake at full Kelly (reference)"
            value={
              result.fullKelly > 0
                ? formatMoney(result.stakeFull, currency)
                : formatMoney(0, currency)
            }
            hint="Most pros stake 25–50% of this"
          />
        </div>
      )}

      {negative && (
        <p className="rounded-md border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
          Kelly fraction is zero or negative — the odds offer no positive expected
          value at your probability estimate. Pass on this bet.
        </p>
      )}

      <details className="surface-card px-5 py-4 text-sm text-muted">
        <summary className="cursor-pointer font-medium text-text">
          How the maths works
        </summary>
        <div className="mt-3 space-y-3">
          <p>
            Full Kelly fraction <code>f* = (b·p − q) / b</code>, where{' '}
            <code>b = decimal_odds − 1</code>, <code>p</code> is your win
            probability and <code>q = 1 − p</code>.
          </p>
          <p>
            Expected value per unit staked is <code>EV = p · decimal_odds − 1</code>.
            Your edge over the bookmaker is <code>p − 1/decimal_odds</code>.
          </p>
          <p>
            Most professionals stake a fraction of <code>f*</code> (typically 25–50%)
            to control variance and tolerate model error. Read the full explainer in
            our{' '}
            <a
              href="../learn/kelly-criterion"
              className="text-accent underline-offset-4 hover:underline"
            >
              Kelly criterion guide
            </a>
            .
          </p>
        </div>
      </details>

      <p className="text-2xs text-muted">
        Educational tool. Not betting advice. Past performance does not guarantee
        future results.
      </p>
    </div>
  );
}

type StatProps = {
  label: string;
  value: string;
  hint?: string;
  tone?: 'positive' | 'negative' | 'neutral';
};

function Stat({ label, value, hint, tone = 'neutral' }: StatProps) {
  const toneCls =
    tone === 'positive'
      ? 'text-emerald-300'
      : tone === 'negative'
        ? 'text-rose-300'
        : 'text-text';
  return (
    <div className="flex flex-col gap-1">
      <span className="text-2xs uppercase tracking-[0.08em] text-muted">
        {label}
      </span>
      <span className={`font-mono text-lg ${toneCls}`}>{value}</span>
      {hint ? <span className="text-2xs text-muted">{hint}</span> : null}
    </div>
  );
}
