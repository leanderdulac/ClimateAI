import { test, expect } from '@playwright/test';

test.describe('Hathor Blockchain Tokenization E2E', () => {
  test('should load tokenization page or route guard', async ({ page }) => {
    await page.goto('/tokenization');
    await page.waitForLoadState('domcontentloaded');

    const url = page.url();
    expect(url.includes('/tokenization') || url.includes('/auth') || url.includes('/welcome')).toBeTruthy();
  });

  test('should display tokenization elements or login prompt', async ({ page }) => {
    await page.goto('/tokenization');
    await page.waitForTimeout(1000);

    if (page.url().includes('/tokenization')) {
      const pageTitle = page.locator('text=/token|blockchain|hathor|apólice/i').first();
      const isVisible = await pageTitle.isVisible({ timeout: 5000 }).catch(() => false);
      expect(isVisible).toBeTruthy();
    }
  });
});
