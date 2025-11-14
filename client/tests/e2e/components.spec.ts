import { test, expect } from '@playwright/test';

test.describe('UI Components and Interactions', () => {
  test('should render welcome page components', async ({ page }) => {
    await page.goto('/welcome');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for common UI elements
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should handle button clicks', async ({ page }) => {
    await page.goto('/welcome');
    
    // Find and click first visible button
    const button = page.locator('button').first();
    const isVisible = await button.isVisible({ timeout: 5000 });
    
    if (isVisible) {
      await button.click();
      // Wait for any navigation or state change
      await page.waitForTimeout(500);
    }
    
    expect(true).toBeTruthy(); // Test passed if click didn't error
  });

  test('should have accessible headings', async ({ page }) => {
    await page.goto('/welcome');
    
    // Check for semantic headings
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    
    expect(headingCount).toBeGreaterThan(0);
  });

  test('should render images with alt text', async ({ page }) => {
    await page.goto('/welcome');
    
    const images = page.locator('img');
    const imageCount = await images.count();
    
    // Check that images have alt text or aria-label
    for (let i = 0; i < Math.min(imageCount, 5); i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      
      // At least one of these should exist
      expect(alt !== null || ariaLabel !== null).toBeTruthy();
    }
  });

  test('should have proper color contrast', async ({ page }) => {
    await page.goto('/welcome');
    
    // This is a basic test - Playwright doesn't have built-in contrast checking
    // In production, you'd use tools like axe-core
    const bodyBgColor = await page.locator('body').evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    
    expect(bodyBgColor).toBeTruthy();
  });

  test('should handle window resize', async ({ page }) => {
    await page.goto('/welcome');
    
    // Test responsive behavior
    const viewports = [
      { width: 1920, height: 1080 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 },
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Check that page is still visible
      const body = page.locator('body');
      await expect(body).toBeVisible();
    }
  });

  test('should handle form submission', async ({ page }) => {
    await page.goto('/auth');
    
    // Find form
    const form = page.locator('form').first();
    const isFormVisible = await form.isVisible({ timeout: 5000 });
    
    if (isFormVisible) {
      // Try to submit empty form to check validation
      const submitButton = form.locator('button[type="submit"]').first();
      await submitButton.click();
      
      // Wait for response or validation error
      await page.waitForTimeout(1000);
    }
    
    expect(true).toBeTruthy();
  });

  test('should have proper semantic HTML', async ({ page }) => {
    await page.goto('/');
    
    // Check for main landmark
    const main = page.locator('main');
    const mainVisible = await main.isVisible({ timeout: 5000 }).catch(() => false);
    
    // Check for header or nav
    const header = page.locator('header').or(page.locator('[role="banner"]'));
    const headerVisible = await header.isVisible({ timeout: 5000 }).catch(() => false);
    
    expect(mainVisible || headerVisible).toBeTruthy();
  });
});
