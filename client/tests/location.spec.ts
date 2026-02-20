import { test, expect } from '@playwright/test';

test('city search suggestions and selection', async ({ page }) => {
  await page.goto('http://localhost:5173/');

  // Find city input by Portuguese placeholder
  const cityInput = page.locator('input[placeholder="Digite o nome da cidade"]');
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
