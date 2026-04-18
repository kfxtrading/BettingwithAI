import type { ReactNode } from 'react';

interface KpiTileProps {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: 'default' | 'positive' | 'negative' | 'accent';
}

const toneClass: Record<NonNullable<KpiTileProps['tone']>, string> = {
  default: 'text-text',
  positive: 'text-positive',
  negative: 'text-negative',
  accent: 'text-accent',
};

export function KpiTile({
  label,
  value,
  hint,
  tone = 'default',
}: KpiTileProps) {
  return (
    <div className="surface-card flex flex-col gap-2 px-5 py-5">
      <span className="text-2xs uppercase tracking-[0.08em] text-muted">
        {label}
      </span>
      <span className={`font-mono text-2xl ${toneClass[tone]}`}>{value}</span>
      {hint && <span className="text-2xs text-muted">{hint}</span>}
    </div>
  );
}
