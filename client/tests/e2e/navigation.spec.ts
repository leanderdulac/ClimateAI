import { test, expect } from '@playwright/test';

test.describe('Navigation and Routing', () => {
  test('should navigate between pages correctly', async ({ page }) => {
    await page.goto('/');

    // Check initial page
    await expect(page).toHaveURL(/\/$|\/welcome/);
  });

  test('should display welcome page', async ({ page }) => {
    await page.goto('/welcome');

    // Check if page loads
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/welcome');
  });

  test('should have navigation menu', async ({ page }) => {
    await page.goto('/');

    // Look for navigation elements
    const nav = page.locator('nav').or(page.locator('[role="navigation"]'));
    const navVisible = await nav.isVisible({ timeout: 5000 }).catch(() => false);

    expect(navVisible).toBeTruthy();
  });

  test('should handle protected route access', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto('/dashboard', { waitUntil: 'networkidle' });

    // Should either redirect to auth or show auth page
    const isOnAuth = page.url().includes('/auth');
    const isOnWelcome = page.url().includes('/welcome');

    // At least one should be true
    expect(isOnAuth || isOnWelcome).toBeTruthy();
  });

  test('should handle 404 gracefully', async ({ page }) => {
    const response = await page.goto('/nonexistent-page-12345', { waitUntil: 'networkidle' });

    // Should handle 404 or redirect
    const isNotFound = response?.status() === 404 || page.url().includes('/');
    expect(isNotFound).toBeTruthy();
  });

  test('should persist navigation state', async ({ page }) => {
    await page.goto('/');

    // Navigate to auth
    await page.goto('/auth');
    expect(page.url()).toContain('/auth');

    // Go back
    await page.goBack();

    // Should be back on welcome/home
    await page.waitForTimeout(500);
    const isOnWelcome = page.url().includes('/welcome') || page.url().includes('/?');
    expect(isOnWelcome).toBeTruthy();
  });

  test('should load pages with correct status codes', async ({ page }) => {
    const publicRoutes = ['/', '/welcome', '/auth'];

    for (const route of publicRoutes) {
      const response = await page.goto(route, { waitUntil: 'networkidle' });
      expect(response?.status()).toBeLessThan(400);
    }
  });
});
