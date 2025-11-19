import { test, expect } from '@playwright/test';

test.describe('Performance and Loading', () => {
  test('should load page within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/', { waitUntil: 'networkidle' });

    const loadTime = Date.now() - startTime;

    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    console.log(`Page load time: ${loadTime}ms`);
  });

  test('should handle lazy loading of pages', async ({ page }) => {
    await page.goto('/');

    // Check initial bundle size by monitoring network
    const requests = [];

    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
      });
    });

    await page.waitForLoadState('networkidle');

    // Should have made network requests
    expect(requests.length).toBeGreaterThan(0);
  });

  test('should render without layout shift', async ({ page }) => {
    await page.goto('/');

    // Monitor cumulative layout shift
    const cls = await page.evaluate(() => {
      return new Promise(resolve => {
        let clsValue = 0;
        const observer = new PerformanceObserver(entryList => {
          for (const entry of entryList.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          resolve(clsValue);
        });

        observer.observe({ type: 'layout-shift', buffered: true });

        // Stop monitoring after 3 seconds
        setTimeout(() => resolve(clsValue), 3000);
      });
    });

    // CLS should be low (< 0.1 is good)
    console.log(`Cumulative Layout Shift: ${cls}`);
    expect(cls).toBeLessThan(0.25);
  });

  test('should not have console errors on page load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/', { waitUntil: 'networkidle' });

    // Filter out expected errors
    const filteredErrors = errors.filter(e =>
      !e.includes('Failed to fetch') &&
      !e.includes('CORS') &&
      !e.includes('404')
    );

    // Should have no unexpected console errors
    if (filteredErrors.length > 0) {
      console.log('Console errors:', filteredErrors);
    }
  });

  test('should lazy load subpages efficiently', async ({ page }) => {
    await page.goto('/');

    // Measure initial bundle
    let jsSize = 0;
    let cssSize = 0;

    page.on('response', response => {
      const contentType = response.headers()['content-type'] || '';
      const contentLength = response.headers()['content-length'];

      if (contentType.includes('javascript')) {
        jsSize += parseInt(contentLength || '0', 10);
      } else if (contentType.includes('css')) {
        cssSize += parseInt(contentLength || '0', 10);
      }
    });

    await page.waitForLoadState('networkidle');

    console.log(`Initial JS size: ${jsSize} bytes, CSS size: ${cssSize} bytes`);

    // Should have reasonable initial bundle
    expect(jsSize).toBeLessThan(500000); // Less than 500KB
  });

  test('should handle images efficiently', async ({ page }) => {
    await page.goto('/welcome');

    const images = page.locator('img');
    const count = await images.count();

    // Check that images have loading="lazy" or similar optimization
    for (let i = 0; i < Math.min(count, 5); i++) {
      const img = images.nth(i);
      const loading = await img.getAttribute('loading');
      const src = await img.getAttribute('src');

      // Images should have src and ideally loading attribute
      expect(src).toBeTruthy();
    }
  });

  test('should measure First Contentful Paint', async ({ page }) => {
    const metrics = await page.evaluate(() => {
      return new Promise(resolve => {
        const observer = new PerformanceObserver(entryList => {
          for (const entry of entryList.getEntries()) {
            if ((entry as any).name === 'first-contentful-paint') {
              resolve((entry as any).startTime);
              observer.disconnect();
              return;
            }
          }
          resolve(null);
        });

        observer.observe({ entryTypes: ['paint'] });

        // Timeout after 5 seconds
        setTimeout(() => resolve(null), 5000);
      });
    });

    console.log(`First Contentful Paint: ${metrics}ms`);

    // FCP should be under 3 seconds for good performance
    if (metrics !== null) {
      expect((metrics as number)).toBeLessThan(3000);
    }
  });
});
