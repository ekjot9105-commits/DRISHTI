import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { defineConfig } from 'vite'

// https://vite.dev/config/
//
// The dev server runs HTTPS with a self-signed cert because browsers only grant
// getUserMedia (the /phone page) on a secure origin — a plain http:// LAN
// address is refused. `host: true` binds 0.0.0.0 so phones on the network can
// reach it.
//
// Everything the app talks to is proxied through this same origin, so the page
// never mixes https content with http/ws requests: the backend stays plain
// HTTP on :8000 behind the proxy and is never contacted directly by the
// browser. /evidence and /data are the backend's StaticFiles mounts (evidence
// snapshots and uploads), which the Evidence Vault and Alert Center load by URL.
const BACKEND = 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/ws': { target: BACKEND, changeOrigin: true, ws: true },
      '/evidence': { target: BACKEND, changeOrigin: true },
      '/data': { target: BACKEND, changeOrigin: true },
    },
  },
})
