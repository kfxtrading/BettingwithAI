import type { FormRow, RatingRow } from '@/lib/types';
import { FormChip } from './FormChip';

interface RatingsTableProps {
  rows: RatingRow[];
  forms?: Record<string, FormRow>;
}

function fmt(value: number): string {
  return (value >= 0 ? '+' : '') + value.toFixed(3);
}

export function RatingsTable({ rows, forms }: RatingsTableProps) {
  return (
    <div className="surface-card overflow-hidden">
      <div className="hidden grid-cols-[3rem_1fr_4rem_4rem_4rem_minmax(8rem,auto)] gap-4 px-5 py-3 text-2xs uppercase tracking-[0.08em] text-muted md:grid">
        <span>#</span>
        <span>Team</span>
        <span className="text-right">Home</span>
        <span className="text-right">Away</span>
        <span className="text-right">Overall</span>
        <span className="text-right">Form</span>
      </div>
      <ul>
        {rows.map((row) => {
          const form = forms?.[row.team];
          return (
            <li
              key={row.team}
              className="hairline grid grid-cols-[3rem_1fr_4rem_4rem_4rem_minmax(8rem,auto)] items-center gap-4 px-5 py-3 text-sm first:border-none"
            >
              <span className="font-mono text-muted">{row.rank}</span>
              <span className="truncate font-medium">{row.team}</span>
              <span className="text-right font-mono">{fmt(row.pi_home)}</span>
              <span className="text-right font-mono">{fmt(row.pi_away)}</span>
              <span className="text-right font-mono">
                {fmt(row.pi_overall)}
              </span>
              <span className="flex justify-end">
                {form ? <FormChip form={form.last5} /> : <span className="text-muted">—</span>}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
