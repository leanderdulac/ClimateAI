import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const publicDir = resolve(__dirname, '../../public');

describe('public GEO files', () => {
  it('keeps robots.txt allowing crawlers and pointing to the sitemap', () => {
    const robots = readFileSync(resolve(publicDir, 'robots.txt'), 'utf8');
    expect(robots).toContain('User-agent: *');
    expect(robots).toContain('Allow: /');
    expect(robots).toContain('Sitemap: https://www.climatewise.com.br/sitemap.xml');
  });

  it('keeps sitemap.xml pointing at the production home', () => {
    const sitemap = readFileSync(resolve(publicDir, 'sitemap.xml'), 'utf8');
    expect(sitemap).toContain('https://www.climatewise.com.br/');
    expect(sitemap).toContain('urlset');
  });

  it('keeps llms.txt with the production ClimateWise brief', () => {
    const llms = readFileSync(resolve(publicDir, 'llms.txt'), 'utf8');
    expect(llms).toContain('# ClimateWise');
    expect(llms).toContain('https://www.climatewise.com.br/');
    expect(llms).toMatch(/climateTech brasileira/i);
  });
});
