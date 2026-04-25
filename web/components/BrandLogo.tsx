import * as React from 'react';

type BrandLogoProps = {
  size?: number;
  className?: string;
  withBackground?: boolean;
  background?: string;
  ballColor?: string;
  padColor?: string;
  rx?: number;
  title?: string;
};

const CX = 50;
const CY = 50;
const BALL_RADIUS = 27;
const CENTER_PAD_SCALE = 0.22;
const RING_RADIUS_SCALE = 0.6;
const RING_PAD_SCALE = 0.16;

function pentagonPoints(cx: number, cy: number, size: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 5; i += 1) {
    const angle = ((-90 + i * 72) * Math.PI) / 180;
    const x = cx + size * Math.cos(angle);
    const y = cy + size * Math.sin(angle);
    pts.push(`${x.toFixed(3)},${y.toFixed(3)}`);
  }
  return pts.join(' ');
}

const PAD_POINTS: string[] = (() => {
  const out: string[] = [];
  out.push(pentagonPoints(CX, CY, BALL_RADIUS * CENTER_PAD_SCALE));
  const ringRadius = BALL_RADIUS * RING_RADIUS_SCALE;
  const ringSize = BALL_RADIUS * RING_PAD_SCALE;
  for (let i = 0; i < 5; i += 1) {
    const angle = ((-90 + i * 72) * Math.PI) / 180;
    const px = CX + ringRadius * Math.cos(angle);
    const py = CY + ringRadius * Math.sin(angle);
    out.push(pentagonPoints(px, py, ringSize));
  }
  return out;
})();

export function BrandLogo({
  size = 20,
  className,
  withBackground = false,
  background = '#0a0a0a',
  ballColor = 'rgb(212,101,74)',
  padColor = '#0a0a0a',
  rx = 20.83,
  title,
}: BrandLogoProps) {
  const titleId = title ? 'brand-logo-title' : undefined;
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 100 100"
      role={title ? 'img' : undefined}
      aria-labelledby={titleId}
      aria-hidden={title ? undefined : true}
      className={className}
    >
      {title ? <title id={titleId}>{title}</title> : null}
      {withBackground ? (
        <rect width="100" height="100" rx={rx} fill={background} />
      ) : null}
      <circle cx={CX} cy={CY} r={BALL_RADIUS} fill={ballColor} />
      <g fill={padColor}>
        {PAD_POINTS.map((points, i) => (
          <polygon key={i} points={points} />
        ))}
      </g>
    </svg>
  );
}

export const BRAND_LOGO_PAD_POINTS = PAD_POINTS;
