import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // A single `npm run build` output now serves both editions: the Web
  // deployment, and the Desktop app (pywebview loads it over
  // http://127.0.0.1:PORT/ from the same FastAPI process — see
  // desktop_app/main.py). Both are plain HTTP, same-origin as the API, so
  // the default absolute base and normal history-mode routing (see
  // src/router/index.js) work unmodified for both.
  server: {
    port: 5173,
    // Dev-only convenience: lets the frontend call relative /api/... paths
    // without hardcoding the backend origin. Production builds instead use
    // VITE_API_BASE_URL (see src/services/api.js) since there is no Vite
    // dev server to proxy through once the app is built as static files.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
