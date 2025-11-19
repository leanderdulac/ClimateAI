import type { embrapaApi as EmbrapaApiInstance } from './embrapaApi';

type EmbrapaApi = typeof EmbrapaApiInstance;

let embrapaApiPromise: Promise<EmbrapaApi> | null = null;

const loadModule = async () => {
  const module = await import('./embrapaApi');
  return module.embrapaApi;
};

export const loadEmbrapaApi = async (): Promise<EmbrapaApi> => {
  if (!embrapaApiPromise) {
    embrapaApiPromise = loadModule();
  }
  return embrapaApiPromise;
};
