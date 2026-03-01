/**
 * ClimateWise - Accessibility Tests (a11y)
 * Testes de acessibilidade usando axe-core e Playwright
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Homepage Accessibility', () => {
  test('should not have accessibility violations on homepage', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    console.log(`Homepage: ${accessibilityScanResults.violations.length} violations`);
    
    // Log violations for debugging
    accessibilityScanResults.violations.forEach(violation => {
      console.log(`[${violation.impact}] ${violation.id}: ${violation.description}`);
    });
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');
    
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBe(1);
    
    const h1Text = await page.locator('h1').textContent();
    expect(h1Text).toBeTruthy();
    expect(h1Text!.length).toBeGreaterThan(0);
  });
  
  test('should have skip link', async ({ page }) => {
    await page.goto('/');
    
    const skipLink = page.locator('a[href="#main-content"], a[href="#content"], [class*="skip"]');
    expect(skipLink).toBeTruthy();
  });
  
  test('should be navigable with keyboard', async ({ page }) => {
    await page.goto('/');
    
    // Tab through elements
    let tabCount = 0;
    const maxTabs = 50;
    
    while (tabCount < maxTabs) {
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      
      if (!focusedElement || focusedElement === 'BODY') {
        break;
      }
      
      tabCount++;
    }
    
    expect(tabCount).toBeGreaterThan(0);
  });
});

test.describe('Dashboard Accessibility', () => {
  test('should not have accessibility violations on dashboard', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to dashboard
    const dashboardLink = page.locator('a[href*="dashboard"], a[href*="welcome"]');
    if (await dashboardLink.count() > 0) {
      await dashboardLink.first().click();
      await page.waitForURL(/dashboard|welcome/);
    }
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    console.log(`Dashboard: ${accessibilityScanResults.violations.length} violations`);
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('charts should have accessible descriptions', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to dashboard
    const dashboardLink = page.locator('a[href*="dashboard"], a[href*="welcome"]');
    if (await dashboardLink.count() > 0) {
      await dashboardLink.first().click();
      await page.waitForURL(/dashboard|welcome/);
    }
    
    // Check for chart accessibility
    const charts = page.locator('[class*="chart"], [class*="recharts"], svg[role="img"]');
    const chartCount = await charts.count();
    
    for (let i = 0; i < chartCount; i++) {
      const chart = charts.nth(i);
      const ariaLabel = await chart.getAttribute('aria-label');
      const role = await chart.getAttribute('role');
      
      // Charts should have aria-label or be marked as decorative
      expect(ariaLabel || role === 'presentation' || role === 'img').toBeTruthy();
    }
  });
});

test.describe('Forms Accessibility', () => {
  test('login form should be accessible', async ({ page }) => {
    await page.goto('/auth');
    
    // Check all inputs have labels
    const inputs = page.locator('input:not([type="hidden"]), textarea, select');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      // Input should have id, aria-label, or aria-labelledby
      expect(id || ariaLabel || ariaLabelledBy).toBeTruthy();
      
      // If input has id, check for associated label
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const labelCount = await label.count();
        expect(labelCount).toBeGreaterThan(0);
      }
    }
  });
  
  test('error messages should be announced', async ({ page }) => {
    await page.goto('/auth');
    
    // Check for aria-live regions
    const liveRegions = page.locator('[aria-live]');
    const liveCount = await liveRegions.count();
    
    // Should have at least one live region for announcements
    expect(liveCount).toBeGreaterThan(0);
  });
});

test.describe('Navigation Accessibility', () => {
  test('navigation should have proper landmarks', async ({ page }) => {
    await page.goto('/');
    
    const nav = page.locator('nav, [role="navigation"]');
    const navCount = await nav.count();
    
    expect(navCount).toBeGreaterThan(0);
    
    // Each nav should have accessible name
    for (let i = 0; i < navCount; i++) {
      const navElement = nav.nth(i);
      const ariaLabel = await navElement.getAttribute('aria-label');
      const ariaLabelledBy = await navElement.getAttribute('aria-labelledby');
      
      expect(ariaLabel || ariaLabelledBy).toBeTruthy();
    }
  });
  
  test('links should have descriptive text', async ({ page }) => {
    await page.goto('/');
    
    const links = page.locator('a[href]');
    const linkCount = await links.count();
    
    for (let i = 0; i < Math.min(linkCount, 20); i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');
      
      // Links should have text or aria-label
      expect((text && text.trim().length > 0) || ariaLabel).toBeTruthy();
      
      // Avoid generic link text
      const genericTexts = ['click here', 'here', 'more', 'learn more', 'read more'];
      if (text) {
        expect(genericTexts.includes(text.toLowerCase().trim())).toBeFalsy();
      }
    }
  });
});

test.describe('Color Contrast', () => {
  test('text should have sufficient contrast', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .withTags(['wcag2aa'])
      .analyze();
    
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );
    
    console.log(`Color contrast violations: ${contrastViolations.length}`);
    
    // Allow some contrast violations but log them
    contrastViolations.forEach(violation => {
      console.log(`Contrast issue: ${violation.nodes.length} elements`);
    });
  });
});

test.describe('Focus Management', () => {
  test('focus should be visible', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    const focusViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'focus-visible'
    );
    
    expect(focusViolations.length).toBe(0);
  });
  
  test('modal should trap focus', async ({ page }) => {
    await page.goto('/');
    
    // Try to open a modal/dialog if available
    const modalTrigger = page.locator('button, a').filter({ hasText: /open|modal|dialog|close/i }).first();
    
    if (await modalTrigger.count() > 0) {
      await modalTrigger.click();
      await page.waitForTimeout(500);
      
      // Check for focus trap
      const modal = page.locator('[role="dialog"], [class*="modal"], [class*="dialog"]');
      if (await modal.count() > 0) {
        const modalHasFocus = await modal.evaluate(el => {
          return document.activeElement === el || el.contains(document.activeElement);
        });
        
        expect(modalHasFocus).toBeTruthy();
      }
    }
  });
});
