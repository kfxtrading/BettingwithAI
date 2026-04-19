'use client';

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type CalibrationBucket = {
  bin_lower: number;
  bin_upper: number;
  n: number;
  predicted_mean: number;
  actual_rate: number;
};

export function CalibrationPlot({ buckets }: { buckets: CalibrationBucket[] }) {
  if (buckets.length === 0) {
    return (
      <div className="surface-card flex h-64 items-center justify-center text-sm text-muted">
        No settled predictions yet — calibration plot will appear once results are graded.
      </div>
    );
  }

  const data = buckets.map((b) => ({
    predicted: b.predicted_mean,
    actual: b.actual_rate,
    n: b.n,
  }));

  return (
    <div className="surface-card h-80 px-2 py-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 24, bottom: 24, left: 8 }}>
          <CartesianGrid
            stroke="rgba(var(--border), var(--border-alpha))"
            strokeDasharray="0"
            vertical={false}
          />
          <XAxis
            dataKey="predicted"
            type="number"
            domain={[0, 1]}
            stroke="rgb(var(--muted))"
            tick={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)' }}
            tickLine={false}
            axisLine={false}
            label={{
              value: 'Predicted probability',
              position: 'insideBottom',
              offset: -8,
              fontSize: 11,
              fill: 'rgb(var(--muted))',
            }}
          />
          <YAxis
            type="number"
            domain={[0, 1]}
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
            formatter={(value: number, name: string) => [
              value.toFixed(3),
              name === 'actual' ? 'Actual rate' : name,
            ]}
          />
          <ReferenceLine
            segment={[
              { x: 0, y: 0 },
              { x: 1, y: 1 },
            ]}
            stroke="rgba(var(--muted), 0.5)"
            strokeDasharray="4 4"
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="rgb(var(--accent))"
            strokeWidth={1.75}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
          <Scatter dataKey="actual" fill="rgb(var(--accent))" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
