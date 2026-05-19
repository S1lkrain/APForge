/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  katex?: {
    renderToString: (
      tex: string,
      options: { displayMode?: boolean; throwOnError?: boolean; strict?: string },
    ) => string;
  };
}
