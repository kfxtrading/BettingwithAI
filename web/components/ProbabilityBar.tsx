interface ProbabilityBarProps {
  home: number;
  draw: number;
  away: number;
  homeLabel?: string;
  awayLabel?: string;
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ProbabilityBar({
  home,
  draw,
  away,
  homeLabel = 'Home',
  awayLabel = 'Away',
}: ProbabilityBarProps) {
  const total = home + draw + away || 1;
  const segments = [
    {
      key: 'home',
      label: homeLabel,
      width: (home / total) * 100,
      tone: 'bg-text/85',
      value: home,
    },
    {
      key: 'draw',
      label: 'Draw',
      width: (draw / total) * 100,
      tone: 'bg-muted/50',
      value: draw,
    },
    {
      key: 'away',
      label: awayLabel,
      width: (away / total) * 100,
      tone: 'bg-accent/85',
      value: away,
    },
  ];

  return (
    <div className="w-full">
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-2">
        {segments.map((seg) => (
          <div
            key={seg.key}
            className={`${seg.tone} h-full transition-[width] ease-ease`}
            style={{ width: `${seg.width}%` }}
            aria-label={`${seg.label} ${pct(seg.value)}`}
          />
        ))}
      </div>
      <div className="mt-2 flex justify-between font-mono text-2xs text-muted">
        <span>H {pct(home)}</span>
        <span>D {pct(draw)}</span>
        <span>A {pct(away)}</span>
      </div>
    </div>
  );
}
