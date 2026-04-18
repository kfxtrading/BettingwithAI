import type { ReactNode } from 'react';

export function Empty({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children?: ReactNode;
}) {
  return (
    <div className="surface-card flex flex-col items-center justify-center px-8 py-16 text-center">
      <p className="text-base font-medium">{title}</p>
      {hint && (
        <p className="mt-2 max-w-md text-sm text-muted">{hint}</p>
      )}
      {children && <div className="mt-6">{children}</div>}
    </div>
  );
}
