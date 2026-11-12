import { chromium } from '@playwright/test';
const [url, out, w, sel, wait] = process.argv.slice(2);
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] }); const p = await b.newPage({ viewport: { width: +w || 1280, height: 900 } });
await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(+wait || 5000);
if (sel) await p.locator(sel).first().screenshot({ path: out }); else await p.screenshot({ path: out, fullPage: true });
await b.close();
