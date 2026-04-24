import '@testing-library/jest-dom'

// Provide a test-time fallback for Vite's import.meta.env
;(globalThis as any).__VITE_API_BASE_URL__ = (globalThis as any).__VITE_API_BASE_URL__ ?? 'http://localhost:8000'
