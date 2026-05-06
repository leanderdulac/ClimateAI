
/* eslint-env node, es2021 */
/* global document, console, process */
import { chromium } from 'playwright';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000/';

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'], headless: true });
  const page = await browser.newPage();
  try {
    const targetUrl = new URL('/demo', BASE_URL).toString();
    await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 20000 });

    // Validate public demo route is rendered with expected showcase content.
    await page.waitForURL(/\/demo(?:\?.*)?$/, { timeout: 10000 });
    await page.waitForSelector('img[alt="Climate Dashboard"]', { timeout: 12000 });
    await page.waitForSelector('img[alt="Digital Atlas 3D Globe"]', { timeout: 12000 });

    const hasHeaderActions = await page.locator('header button').count();
    if (hasHeaderActions < 2) {
      throw new Error('Expected demo header action buttons not found');
    }

    console.log('FRONTEND TEST: PASS - /demo rendered expected showcase elements');
  } catch (err) {
    console.error('FRONTEND TEST: ERROR', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
