'use client';

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { BankrollPoint } from '@/lib/types';

export function BankrollChart({ data }: { data: BankrollPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="surface-card flex h-64 items-center justify-center text-sm text-muted">
        No bankroll data yet — log some bets to start tracking.
      </div>
    );
  }

  return (
    <div className="surface-card h-72 px-2 py-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 24, bottom: 8, left: 8 }}>
          <CartesianGrid
            stroke="rgba(var(--border), var(--border-alpha))"
            strokeDasharray="0"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            stroke="rgb(var(--muted))"
            tick={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="rgb(var(--muted))"
            tick={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)' }}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            contentStyle={{
              background: 'rgb(var(--surface))',
              border: '1px solid rgba(var(--border), var(--border-alpha))',
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: 'rgb(var(--muted))' }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="rgb(var(--accent))"
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 4, fill: 'rgb(var(--accent))' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
