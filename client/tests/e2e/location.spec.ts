import { test, expect } from '@playwright/test';

test('city search suggestions and selection', async ({ page }) => {
  // Mock authentication by setting localStorage
  await page.addInitScript(() => {
    localStorage.setItem('supabase.auth.token', JSON.stringify({
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      user: { id: 'test-user', email: 'test@example.com' }
    }));
  });

  await page.goto('/dashboard');

  // Find city input by Portuguese placeholder
  const cityInput = page.locator('input').filter({ hasText: /cidade/i }).or(page.locator('input[placeholder*="cidade"]'));
  await expect(cityInput).toBeVisible();

  await cityInput.fill('Salvador');

  // Wait for suggestions to appear and contain 'Salvador'
  const suggestion = page.getByText('Salvador').first();
  await expect(suggestion).toBeVisible({ timeout: 5000 });

  // Click the suggestion and expect that coordinates or formatted address appear
  await suggestion.click();

  // After selection, ensure reverse-geocoded formatted address is visible
  await expect(page.getByText('Salvador - BA, Brasil')).toBeVisible({ timeout: 5000 });
});
