import { chromium } from 'playwright';

const url = process.env.URL || 'http://localhost:3000/en';
const out = process.env.OUT || 'landing-pinterest-2x3.png';

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1000, height: 1500 },
  deviceScaleFactor: 2,
  locale: 'en-US',
});
await context.addInitScript(() => {
  try {
    window.localStorage.setItem(
      'bwai.cookie-consent.v1',
      JSON.stringify({
        accepted: true,
        categories: ['necessary', 'analytics', 'marketing'],
        version: '1.0',
        savedAt: new Date().toISOString(),
      }),
    );
  } catch {}
});
const page = await context.newPage();
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1000, height: 1500 } });
await browser.close();
console.log('Saved', out);
