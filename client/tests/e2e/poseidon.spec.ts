import { test, expect } from '@playwright/test';

test.describe('Poseidon CCO AI Orchestrator E2E', () => {
  test('should load poseidon page or route guard', async ({ page }) => {
    await page.goto('/poseidon');
    await page.waitForLoadState('domcontentloaded');

    const url = page.url();
    expect(url.includes('/poseidon') || url.includes('/auth') || url.includes('/welcome')).toBeTruthy();
  });

  test('should render poseidon interface if authenticated', async ({ page }) => {
    await page.goto('/poseidon');
    await page.waitForTimeout(1000);

    if (page.url().includes('/poseidon')) {
      const poseidonTitle = page.locator('text=/poseidon|cco|orquestrador|atuary/i').first();
      const isVisible = await poseidonTitle.isVisible({ timeout: 5000 }).catch(() => false);
      expect(isVisible).toBeTruthy();
    }
  });
});
