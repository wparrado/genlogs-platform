import '@testing-library/jest-dom';

// Provide a test-time fallback for Vite's import.meta.env
;(globalThis as any).__VITE_API_BASE_URL__ = (globalThis as any).__VITE_API_BASE_URL__ ?? 'https://genlogs-backend-347212169781.us-central1.run.app'
