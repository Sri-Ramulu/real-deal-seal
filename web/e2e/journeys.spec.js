import { test, expect } from '@playwright/test';

const errors = [];
test.beforeEach(({ page }) => {
  errors.length = 0;
  page.on('pageerror', (e) => errors.push(e.message));
});
test.afterEach(() => expect(errors, 'no script errors on the page').toEqual([]));

test('home tells the story and links to the seal check, not to joining', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('Small shops');
  await expect(page.locator('a[href="/join"]')).toHaveCount(0);
  await expect(page.getByRole('link', { name: /Take the 3-minute tour/ })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Why PayPal', exact: true })).toHaveAttribute('href', '/business');
  await expect(page.getByRole('link', { name: 'Check a seal' }).first()).toBeVisible();
});

test('shop cards show a product image, and labels and prices stay inside the card', async ({ page }) => {
  await page.goto('/shop');
  const cards = page.locator('button.offer');
  await expect(cards.first()).toBeVisible();
  const n = await cards.count();
  expect(n).toBeGreaterThan(20);
  for (let i = 0; i < n; i++) {
    const card = cards.nth(i);
    await card.scrollIntoViewIfNeeded();
    const img = card.locator('img.thumb');
    await expect(img).toHaveAttribute('alt', /.+/);
    expect(await img.evaluate((el) => el.complete && el.naturalWidth > 0)).toBe(true);
    const box = await card.boundingBox();
    for (const sel of ['.chip', '.price']) {
      const b = await card.locator(sel).first().boundingBox();
      expect(b.x + b.width, `${sel} inside card ${i}`).toBeLessThanOrEqual(box.x + box.width + 1);
    }
  }
});

test('the assistant shows trust labels with evidence on, and none with evidence off', async ({ page }) => {
  await page.goto('/assistant');
  await page.getByRole('button', { name: /lavender for our guest room/ }).click();
  const on = page.locator('.msg.bot').last();
  await expect(on.locator('article').first()).toBeVisible();
  await expect(on.locator('.chip').first()).toBeVisible();
  await expect(on.getByRole('link', { name: "Open the shop's passport" }).first()).toBeVisible();
  await expect(on.locator('img.pic').first()).toBeVisible();

  await page.locator('label.toggle').click();
  await expect(page.getByText('Evidence off', { exact: true })).toBeVisible();
  await page.getByPlaceholder('What are you shopping for?').fill('purple table runner');
  await page.getByRole('button', { name: /Send/ }).click();
  const off = page.locator('.msg.bot').last();
  await expect(off).toContainText('evidence off');
  await expect(off.locator('article').first()).toBeVisible();
  await expect(off.locator('.chip')).toHaveCount(0);
  await expect(off.locator('.warn')).toHaveCount(0);
  await expect(off.getByRole('link', { name: "Open the shop's passport" })).toHaveCount(0);
});

test('a seal checks out, fails when edited, and the forged badge is caught', async ({ page }) => {
  await page.goto('/verify');
  await page.getByRole('button', { name: /Lydia/ }).click();
  await page.getByRole('button', { name: /Check this seal/ }).click();
  await expect(page.getByText('Genuine').first()).toBeVisible();
  await page.getByRole('button', { name: /Change one number/ }).click();
  await expect(page.getByText('Edited').first()).toBeVisible();
  await page.getByRole('button', { name: /Linen Palace/ }).click();
  await page.getByRole('button', { name: /Check this seal/ }).click();
  await expect(page.getByText('Forged').first()).toBeVisible();
});

test('buying opens a checkout that is clearly labeled as simulated without PayPal keys', async ({ page }) => {
  await page.goto('/shop');
  await page.locator('button.offer', { hasText: 'Cushion cover 18in, Plum' }).filter({ hasText: 'Lydia Linen' }).click();
  await page.locator('.sheet button.btn').click();
  await expect(page).toHaveURL(/checkout\/simulated/);
  await expect(page.locator('body')).toContainText(/simulated/i);
});

test('Merchant Studio opens a demo shop with only the story tabs, and the coach adds tracking', async ({ page }) => {
  await page.goto('/join');
  await expect(page).toHaveURL(/\/studio$/);
  await page.getByRole('button', { name: /Martha/ }).click();
  await expect(page).toHaveURL(/\/studio\/martha/);
  const tabs = page.getByRole('navigation', { name: 'Studio sections' });
  await expect(tabs.getByRole('link')).toHaveText(['Overview', 'Passport', 'Evidence', 'Coach', 'Orders']);
  await tabs.getByRole('link', { name: 'Coach' }).click();
  const add = page.getByRole('button', { name: 'Add tracking' }).first();
  await expect(add).toBeVisible();
  await add.click();
  await expect(page.locator('body')).toContainText(/40 of 48|recorded/);
});

test('the home page shows the same question answered with Evidence off and on, and can run it live', async ({ page }) => {
  await page.goto('/');
  const sbs = page.locator('#difference');
  await expect(sbs.locator('article.off .shop')).toHaveText('Violet & Vine Home');
  await expect(sbs.locator('article.off')).toContainText('Seal withdrawn');
  await expect(sbs.locator('article.on .shop')).toHaveText('Lydia Linen Co.');
  await sbs.getByRole('button', { name: 'A white enamel tea kettle.' }).click();
  await expect(sbs.locator('article.off .shop')).toHaveText('Juniper & Oak Goods');
  await sbs.getByRole('button', { name: /Run it live/ }).click();
  await expect(sbs.getByRole('button', { name: /Run it again/ })).toBeVisible({ timeout: 30000 });
  await expect(sbs.locator('article.on')).toContainText(/It picked|no pick/);
});

test('the judges page walks the five steps, and Why PayPal wins separates measured from proposed', async ({ page }) => {
  await page.goto('/judges');
  await expect(page.locator('ol.steps li')).toHaveCount(5);
  await expect(page.getByRole('link', { name: /Run it live/ })).toHaveAttribute('href', '/#difference');
  await page.goto('/business');
  await expect(page.locator('h1')).toHaveText('Why PayPal wins');
  await expect(page.locator('.wins article')).toHaveCount(4);
  await expect(page.locator('.wins .proj')).toContainText('not measured');
});
