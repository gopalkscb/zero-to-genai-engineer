import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Local: Vite on :5173 proxies to uvicorn on :8000.
// Docker Compose sets VITE_PROXY_TARGET=http://backend:8000 so the
// frontend container can reach the API service by name.
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': proxyTarget,
      '/health': proxyTarget,
    },
  },
});
