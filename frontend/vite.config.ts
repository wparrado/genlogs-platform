import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    // Provide a fallback for Vite's bundled dev flag to avoid ReferenceError in some environments
    __BUNDLED_DEV__: JSON.stringify(false),
  },
  server: {
    port: 5173,
    // Proxy API calls to the backend to avoid CORS during local development.
    // When running in Docker, FRONTEND_PROXY (set in docker-compose) will point to the backend service.
    proxy: {
      '/api': {
        target: process.env.FRONTEND_PROXY || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
