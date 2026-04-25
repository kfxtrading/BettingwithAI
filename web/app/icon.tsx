import { ImageResponse } from 'next/og';

// Next.js App Router: this file becomes /icon at a crawlable URL
// and is emitted as a PNG (Google favicon fetcher prefers PNG over SVG).
export const runtime = 'edge';
export const size = { width: 512, height: 512 };
export const contentType = 'image/png';

const CX = 50;
const CY = 50;
const BALL_RADIUS = 27;
const CENTER_PAD_SCALE = 0.22;
const RING_RADIUS_SCALE = 0.6;
const RING_PAD_SCALE = 0.16;

function pentagonPoints(cx: number, cy: number, s: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 5; i += 1) {
    const angle = ((-90 + i * 72) * Math.PI) / 180;
    const x = cx + s * Math.cos(angle);
    const y = cy + s * Math.sin(angle);
    pts.push(`${x.toFixed(3)},${y.toFixed(3)}`);
  }
  return pts.join(' ');
}

function buildPadPoints(): string[] {
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
}

export default function Icon() {
  const pads = buildPadPoints();
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0a0a0a',
          borderRadius: 96,
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="512"
          height="512"
          viewBox="0 0 100 100"
        >
          <circle cx={CX} cy={CY} r={BALL_RADIUS} fill="rgb(212,101,74)" />
          <g fill="#0a0a0a">
            {pads.map((points, i) => (
              <polygon key={i} points={points} />
            ))}
          </g>
        </svg>
      </div>
    ),
    { ...size },
  );
}
