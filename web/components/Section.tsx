import type { ReactNode } from 'react';

interface SectionProps {
  title?: string;
  caption?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Section({
  title,
  caption,
  action,
  children,
  className = '',
}: SectionProps) {
  return (
    <section className={`mt-14 first:mt-0 ${className}`}>
      {(title || action) && (
        <header className="mb-5 flex items-end justify-between gap-6">
          <div>
            {title && (
              <h2 className="text-xl font-medium tracking-tight">{title}</h2>
            )}
            {caption && (
              <p className="mt-1 text-sm text-muted">{caption}</p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
