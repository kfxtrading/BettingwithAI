'use client';

import { motion } from 'framer-motion';
import type { League } from '@/lib/types';

interface LeagueSwitcherProps {
  leagues: League[];
  value: string | null;
  onChange: (key: string | null) => void;
}

export function LeagueSwitcher({
  leagues,
  value,
  onChange,
}: LeagueSwitcherProps) {
  const options = [{ key: null as string | null, label: 'All' }, ...leagues.map((l) => ({ key: l.key, label: l.code }))];

  return (
    <div
      role="tablist"
      aria-label="League selector"
      className="surface-card relative inline-flex rounded-full p-1"
    >
      {options.map((opt) => {
        const active = value === opt.key;
        return (
          <button
            key={opt.key ?? 'all'}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.key)}
            className="relative isolate rounded-full px-3.5 py-1.5 text-xs font-medium tracking-wide focus-ring press"
          >
            {active && (
              <motion.span
                layoutId="league-switcher-pill"
                className="absolute inset-0 -z-10 rounded-full bg-surface-2"
                transition={{
                  type: 'spring',
                  stiffness: 400,
                  damping: 32,
                }}
              />
            )}
            <span className={active ? 'text-text' : 'text-muted'}>
              {opt.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
