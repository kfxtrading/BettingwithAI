'use client';

import { useId, useState, type ReactNode } from 'react';

interface InfoTooltipProps {
  label: string;
  children: ReactNode;
}

export function InfoTooltip({ label, children }: InfoTooltipProps) {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <span
      className="relative inline-flex align-middle"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={label}
        aria-describedby={open ? id : undefined}
        className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-muted/40 text-2xs font-medium italic text-muted transition-colors hover:border-accent hover:text-accent focus-ring"
      >
        i
      </button>
      <span
        id={id}
        role="tooltip"
        hidden={!open}
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-72 -translate-x-1/2 rounded-lg bg-surface px-4 py-3 text-xs leading-relaxed text-muted shadow-soft"
      >
        {children}
      </span>
    </span>
  );
}
