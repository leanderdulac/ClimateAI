import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import faqpage from '../../../docs/geo/schema/faqpage.json';

const html = readFileSync(resolve(__dirname, '../../index.html'), 'utf8');

function parseJsonLdBlocks(source: string): Record<string, unknown>[] {
  const blocks = [...source.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
  return blocks.map((match) => JSON.parse(match[1]) as Record<string, unknown>);
}

describe('home index.html GEO', () => {
  const schemas = parseJsonLdBlocks(html);

  it('declares lang="pt-BR" on the root html element', () => {
    expect(html).toMatch(/<html lang="pt-BR">/);
  });

  it('keeps title and description in Portuguese', () => {
    expect(html).toContain('<title>ClimateWise AI - Plataforma de Análise Climática</title>');
    expect(html).toContain('content="Plataforma avançada para análise e precificação de eventos climáticos"');
  });

  it('embeds valid Organization and FAQPage JSON-LD in the initial HTML', () => {
    const types = schemas.map((schema) => schema['@type']);
    expect(types).toContain('Organization');
    expect(types).toContain('FAQPage');

    const organization = schemas.find((schema) => schema['@type'] === 'Organization');
    expect(organization?.name).toBe('ClimateWise');
    expect(organization?.url).toBe('https://www.climatewise.com.br');
    expect(organization?.sameAs).toEqual(['https://github.com/leanderdulac/ClimateAI']);
    expect(String(organization?.description)).toMatch(/climateTech brasileira/i);

    const faq = schemas.find((schema) => schema['@type'] === 'FAQPage');
    expect(faq?.url).toBe('https://www.climatewise.com.br/');
    expect(faq?.inLanguage).toBe('pt-BR');
    expect(faq?.mainEntity).toEqual(faqpage.mainEntity);
  });
});
