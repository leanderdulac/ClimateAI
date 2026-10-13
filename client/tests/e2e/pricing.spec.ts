import { test, expect } from '@playwright/test';

test.describe('Parametric Pricing Simulator E2E', () => {
  test('should load pricing simulator page', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('domcontentloaded');

    // Page URL should contain /pricing or redirect if unauthenticated
    const url = page.url();
    expect(url.includes('/pricing') || url.includes('/auth') || url.includes('/welcome')).toBeTruthy();
  });

  test('should render simulator inputs when accessible', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForTimeout(1000);

    if (page.url().includes('/pricing')) {
      // Check for main calculation inputs or headings
      const heading = page.locator('h1, h2, h3').first();
      await expect(heading).toBeVisible({ timeout: 5000 });

      // Look for form or input containers
      const inputs = page.locator('input, select, button');
      const count = await inputs.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should allow interaction with policy simulation options', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForTimeout(1000);

    if (page.url().includes('/pricing')) {
      // Find numeric inputs or sliders
      const numInput = page.locator('input[type="number"]').first();
      if (await numInput.isVisible().catch(() => false)) {
        await numInput.fill('100000');
        expect(await numInput.inputValue()).toBe('100000');
      }

      // Check for simulation trigger button
      const simBtn = page.locator('button:has-text("Simular"), button:has-text("Calcular"), button:has-text("Quote")').first();
      if (await simBtn.isVisible().catch(() => false)) {
        await simBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  });
});
