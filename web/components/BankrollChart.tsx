'use client';

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { BankrollPoint } from '@/lib/types';
import { useLocale } from '@/lib/i18n/LocaleProvider';

export function BankrollChart({ data }: { data: BankrollPoint[] }) {
  const { t } = useLocale();
  if (data.length === 0) {
    return (
      <div className="surface-card flex h-64 items-center justify-center text-sm text-muted">
        {t('bankroll.empty')}
      </div>
    );
  }

  const hasValueSeries = data.some(
    (p) => p.value_bets !== undefined && p.value_bets !== null,
  );
  const hasPredictionSeries = data.some(
    (p) => p.predictions !== undefined && p.predictions !== null,
  );
  const showSplit = hasValueSeries || hasPredictionSeries;

  const nameValueBets = t('bankroll.series.valueBets');
  const namePredictions = t('bankroll.series.predictions');
  const nameCombined = t('bankroll.series.combined');

  return (
    <div className="surface-card h-80 px-2 py-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 48, bottom: 8, left: 8 }}>
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
            padding={{ left: 8, right: 16 }}
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
          {showSplit ? (
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
              iconType="plainline"
            />
          ) : null}

          {showSplit ? (
            <>
              {hasValueSeries ? (
                <Line
                  type="monotone"
                  dataKey="value_bets"
                  name={nameValueBets}
                  stroke="rgb(var(--accent))"
                  strokeWidth={1.75}
                  dot={false}
                  activeDot={{ r: 4, fill: 'rgb(var(--accent))' }}
                  connectNulls
                />
              ) : null}
              {hasPredictionSeries ? (
                <Line
                  type="monotone"
                  dataKey="predictions"
                  name={namePredictions}
                  stroke="rgb(var(--muted))"
                  strokeWidth={1.75}
                  dot={false}
                  activeDot={{ r: 4, fill: 'rgb(var(--muted))' }}
                  connectNulls
                />
              ) : null}
              <Line
                type="monotone"
                dataKey="value"
                name={nameCombined}
                stroke="rgb(var(--muted))"
                strokeOpacity={0.55}
                strokeWidth={1.25}
                strokeDasharray="4 4"
                dot={false}
                activeDot={false}
                connectNulls
              />
            </>
          ) : (
            <Line
              type="monotone"
              dataKey="value"
              name={nameCombined}
              stroke="rgb(var(--accent))"
              strokeWidth={1.75}
              dot={false}
              activeDot={{ r: 4, fill: 'rgb(var(--accent))' }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
