import { describe, expect, it } from 'vitest';

import { isFeatureEnabled } from './features';

describe('features', () => {
  it('enables atlas, tokenization, assistant and analytics by default', () => {
    expect(isFeatureEnabled('atlas')).toBe(true);
    expect(isFeatureEnabled('tokenization')).toBe(true);
    expect(isFeatureEnabled('assistant')).toBe(true);
    expect(isFeatureEnabled('analytics')).toBe(true);
  });
});
