import { ImageResponse } from 'next/og';

// Next.js App Router: this file becomes /icon at a crawlable URL
// and is emitted as a PNG (Google favicon fetcher prefers PNG over SVG).
export const runtime = 'edge';
export const size = { width: 512, height: 512 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgb(250,248,245)',
          borderRadius: 96,
        }}
      >
        <div
          style={{
            width: 280,
            height: 280,
            borderRadius: '50%',
            background: 'rgb(212,101,74)',
          }}
        />
      </div>
    ),
    { ...size },
  );
}
