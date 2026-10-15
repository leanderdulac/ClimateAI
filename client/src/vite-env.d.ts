/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_URL?: string;
  readonly VITE_USE_MOCK_DATA?: string;
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_ANON_KEY?: string;
  readonly VITE_BASE_EXPLORER_URL?: string;
  readonly VITE_ENABLE_ANALYTICS?: string;
  readonly VITE_ENABLE_TOKENIZATION?: string;
  readonly VITE_ENABLE_ATLAS?: string;
  readonly VITE_ENABLE_ASSISTANT?: string;
  readonly VITE_ENABLE_WEATHERNEXT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
