// Records a captioned walkthrough of the running app with Playwright. Usage (server on :8000, samples seeded):
//   node scripts/record_walkthrough.mjs [outDir]     then convert the .webm with ffmpeg (see docs/video-script.md)
// The captions are an overlay added by this script; everything else on screen is the real application.
import { chromium } from 'playwright';

const BASE = process.env.RDS_URL ?? 'http://localhost:8000';
const out = process.argv[2] ?? 'docs/video';
const browser = await chromium.launch({ executablePath: process.env.CHROME ?? undefined, args: ['--no-sandbox'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: out, size: { width: 1280, height: 720 } } });
const page = await ctx.newPage();
const wait = (ms) => page.waitForTimeout(ms);

async function caption(text) {
  await page.evaluate((t) => {
    let el = document.getElementById('rds-caption');
    if (!el) {
      el = document.createElement('div');
      el.id = 'rds-caption';
      el.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:99999;max-width:980px;width:max-content;background:#0a0a0a;color:#fff;' +
        'font:500 21px/1.35 "Instrument Sans Variable",Arial,sans-serif;padding:14px 22px;border-radius:6px;box-shadow:0 10px 40px rgba(0,0,0,.35);text-align:center;transition:opacity .3s';
      document.body.appendChild(el);
    }
    el.style.opacity = t ? '1' : '0';
    el.textContent = t;
  }, text);
}
async function go(path, text, hold = 2500) { await page.goto(BASE + path, { waitUntil: 'networkidle' }); await wait(500); await caption(text); await wait(hold); }
async function scroll(px, ms = 1600) { const steps = 40; for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, px / steps); await wait(ms / steps); } }

await go('/', 'Ask an AI assistant for a table runner and it picks the chain it recognises.', 4500);
await caption('Real Deal Seal gives the same assistant proof to read. Now it picks Lydia.'); await wait(4500);
await scroll(1150); await caption('The problem is measured: a 2026 Lightspeed study found assistants pick the big retailer about nine times in ten.'); await wait(6000);

await go('/shops/lydia', 'A Merchant Passport is counts, not a score. 100 PayPal sandbox orders behind it.', 4000);
await scroll(800); await caption('Each rule shows what was counted, out of how many.'); await wait(3500);
await scroll(650); await caption('Each fact says where it came from: PayPal record, reported by the shop, or simulated for this demo.'); await wait(5000);

await go('/verify?shop=lydia', 'The passport is signed. Code checks it against a published key: genuine.', 4500);
await page.click('text=Change one number, then check'); await caption('Change one number and the signature stops matching.'); await wait(4500);
await page.click('button:has-text("Linen Palace")'); await caption('This shop shows a badge signed by a key nobody publishes: forged.'); await wait(4500);

await go('/assistant', 'The assistant searches, then shows each shop’s standing beside the price.', 1500);
await page.fill('form input', 'purple table runner for my dining table'); await wait(600); await page.click('form button'); await page.waitForSelector('article'); await wait(1200);
await caption('This recording runs offline (no model key): a plain search with evidence. With a key, Claude reads each passport with eight tools.'); await wait(6500);
await caption('It flags a listing that tries to give instructions to AI assistants.'); await scroll(260, 900); await wait(3500);
await page.click('article:has-text("Lydia") button'); await page.waitForURL(/checkout\/simulated/); await wait(600);
await caption('Buying: the agent can open a checkout, but only the buyer can approve it. (Simulated here: no PayPal keys on this machine.)'); await wait(5500);
await page.click('text=Approve the simulated payment'); await page.waitForSelector('h1:has-text("Paid")');
await caption('In PayPal mode the server asks PayPal whether the exact amount was captured before it says paid.'); await wait(5500);

await go('/studio', 'Merchant Studio: a private workspace for each business.', 2000);
await page.click('button:has-text("Martha")'); await page.waitForURL(/studio\/martha/); await wait(1200);
await caption('Martha misses four rules, and the studio says which, with the count behind each.'); await wait(5000);
await page.click('button.kpi.click'); await page.waitForSelector('.grid-host .ag-row'); await caption('One click shows the exact orders behind the number, in AG Grid.'); await wait(5000);
await go('/studio/martha?tab=coach', 'The coach turns each unmet rule into work she can do here.', 3000);
await page.fill('.fix form input', '1Z999AA10123456784'); await wait(700); await page.click('.fix form button'); await page.waitForSelector('.notice:has-text("Recorded")', { timeout: 30000 });
await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await caption('She adds a tracking number. The record is rebuilt and the count moves from 39 to 40 of 48.'); await wait(6000);
await go('/studio/martha?tab=readiness', 'Business readiness: a signed statement of records she can share with one recipient, and take back.', 5500);

await go('/shops/bright-clean-co', 'Any business can join with no code. A cleaner is judged on finished jobs, not parcels.', 5000);
await caption('Records a business uploads itself are labelled that way. They cannot earn the seal.'); await scroll(700); await wait(4000);

await go('/scorecard', 'Does it work? 50 requests, run twice. With evidence, small shops won 37 instead of 25.', 6000);
await scroll(900); await caption('A balanced scorecard: every number names the measure it came from. Red is off target.'); await wait(5500);

await go('/developers', 'Underneath: eight tools any agent can use over MCP.', 3500);
await scroll(1500, 2200); await caption('Gold is a star schema with data contracts. 303 rules are checked on every build.'); await wait(5500);
await go('/proof', 'Every claim is mapped to the tests that prove it.', 1500);
await page.evaluate(() => [...document.querySelectorAll('h2')].find((h) => h.textContent.includes('Every claim'))?.scrollIntoView({ behavior: 'smooth', block: 'start' })); await wait(5000);
await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })); await caption('Real Deal Seal. Proof beats brand.'); await wait(5000);

await ctx.close();
await browser.close();
console.log('recorded to', out);
