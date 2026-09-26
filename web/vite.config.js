import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages serves the site from /japan-fiscal-lens/.
export default defineConfig({
  plugins: [vue()],
  base: process.env.NODE_ENV === 'production' ? '/japan-fiscal-lens/' : '/',
  // ECharts core is ~630 kB (≈215 kB gzipped) even tree-shaken; that is expected.
  build: { chunkSizeWarningLimit: 700 },
})
