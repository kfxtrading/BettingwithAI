'use client';

import { useMemo } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { EquityIndexPoint } from '@/lib/types';

const BASELINE = 100;

type Row = {
  date: string;
  index: number;
  n_bets_cumulative: number;
  above: number | null;
  below: number | null;
};

function aggregate(
  points: EquityIndexPoint[],
): EquityIndexPoint[] {
  if (points.length <= 500) return points;
  const groupSize = points.length > 2000 ? 30 : 7;
  const out: EquityIndexPoint[] = [];
  for (let i = 0; i < points.length; i += groupSize) {
    const chunk = points.slice(i, i + groupSize);
    const last = chunk[chunk.length - 1];
    const avg =
      chunk.reduce((s, p) => s + p.index, 0) / chunk.length;
    out.push({
      date: last.date,
      index: Math.round(avg * 100) / 100,
      n_bets_cumulative: last.n_bets_cumulative,
    });
  }
  return out;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('de-DE', {
    month: 'short',
    year: '2-digit',
  }).format(d);
}

function formatTooltipDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(d);
}

interface TooltipPayload {
  payload?: Row;
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0]?.payload;
  if (!row) return null;
  return (
    <div
      className="surface-card px-3 py-2 text-xs"
      style={{ minWidth: 160 }}
    >
      <div className="text-muted">{formatTooltipDate(row.date)}</div>
      <div className="mt-1 font-mono text-sm">
        Index <strong>{row.index.toFixed(2)}</strong>
      </div>
      <div className="text-muted">
        {row.n_bets_cumulative} Spiele kumuliert
      </div>
    </div>
  );
}

export function PerformanceIndexChart({
  data,
}: {
  data: EquityIndexPoint[];
}) {
  const rows = useMemo<Row[]>(() => {
    const aggregated = aggregate(data);
    return aggregated.map((p) => ({
      date: p.date,
      index: p.index,
      n_bets_cumulative: p.n_bets_cumulative,
      above: p.index >= BASELINE ? p.index : BASELINE,
      below: p.index < BASELINE ? p.index : BASELINE,
    }));
  }, [data]);

  if (rows.length < 2) {
    return (
      <div className="surface-card flex h-72 items-center justify-center px-6 text-center text-sm text-muted">
        Noch zu wenige Datenpunkte, um einen Verlauf darzustellen.
      </div>
    );
  }

  return (
    <div className="surface-card h-80 px-2 py-4">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={rows}
          margin={{ top: 12, right: 24, bottom: 8, left: 8 }}
        >
          <defs>
            <linearGradient id="pi-above" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="rgb(var(--positive))"
                stopOpacity={0.35}
              />
              <stop
                offset="100%"
                stopColor="rgb(var(--positive))"
                stopOpacity={0}
              />
            </linearGradient>
            <linearGradient id="pi-below" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor="rgb(var(--negative))"
                stopOpacity={0}
              />
              <stop
                offset="100%"
                stopColor="rgb(var(--negative))"
                stopOpacity={0.35}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            stroke="rgba(var(--border), var(--border-alpha))"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            stroke="rgb(var(--muted))"
            tick={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatDate}
            interval="preserveStartEnd"
            minTickGap={48}
          />
          <YAxis
            stroke="rgb(var(--muted))"
            tick={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)' }}
            tickLine={false}
            axisLine={false}
            width={48}
            domain={['auto', 'auto']}
          />
          <ReferenceLine
            y={BASELINE}
            stroke="rgb(var(--muted))"
            strokeDasharray="4 4"
            strokeOpacity={0.6}
          />
          <Area
            type="monotone"
            dataKey="above"
            stroke="none"
            fill="url(#pi-above)"
            baseValue={BASELINE}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="below"
            stroke="none"
            fill="url(#pi-below)"
            baseValue={BASELINE}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="index"
            stroke="rgb(var(--accent))"
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 4, fill: 'rgb(var(--accent))' }}
            isAnimationActive={false}
          />
          <Tooltip content={<ChartTooltip />} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
