interface FormChipProps {
  result: string;
}

const tone: Record<string, string> = {
  W: 'bg-positive text-white',
  D: 'bg-surface-2 text-muted',
  L: 'bg-negative/85 text-white',
};

export function FormChip({ form }: { form: string }) {
  return (
    <div className="inline-flex gap-1">
      {form.split('').map((r, i) => (
        <span
          key={i}
          className={`flex h-5 w-5 items-center justify-center rounded-sm font-mono text-2xs ${
            tone[r] ?? 'bg-surface-2 text-muted'
          }`}
        >
          {r}
        </span>
      ))}
    </div>
  );
}
