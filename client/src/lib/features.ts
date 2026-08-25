function envFlag(name: keyof ImportMetaEnv, defaultEnabled = true): boolean {
  const raw = import.meta.env[name];
  if (raw === undefined || raw === '') {
    return defaultEnabled;
  }
  return String(raw).toLowerCase() === 'true';
}

export const features = {
  atlas: envFlag('VITE_ENABLE_ATLAS'),
  tokenization: envFlag('VITE_ENABLE_TOKENIZATION'),
  assistant: envFlag('VITE_ENABLE_ASSISTANT'),
  analytics: envFlag('VITE_ENABLE_ANALYTICS'),
};

export type FeatureName = keyof typeof features;

export function isFeatureEnabled(name: FeatureName): boolean {
  return features[name];
}
