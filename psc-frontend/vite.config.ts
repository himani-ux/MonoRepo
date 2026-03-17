import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import { fileURLToPath, URL } from 'node:url';

/**
 * Vite configuration for PSC Inspection Module.
 *
 * Source: TECH_STACK.md §1.1 (Vite 5.4.0)
 * PWA: TECH_STACK.md §1.10 (vite-plugin-pwa 0.20.0)
 * Design: DESIGN_SYSTEM.md §1 (theme-color primary-500)
 */
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      registerType: 'prompt',
      injectRegister: false,
      manifest: {
        name: 'PSC Inspection Module',
        short_name: 'PSC',
        description: 'Port State Control, RightShip, and Audit inspection management',
        theme_color: '#3B82F6',
        background_color: '#FFFFFF',
        display: 'standalone',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-192x192.svg',
            sizes: '192x192',
            type: 'image/svg+xml',
          },
          {
            src: '/icons/icon-512x512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
          },
          {
            src: '/icons/icon-512x512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
      injectManifest: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff,woff2}'],
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-select',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-label',
            '@radix-ui/react-slot',
            '@radix-ui/react-toast',
            '@radix-ui/react-tabs',
            '@radix-ui/react-dropdown-menu',
            'lucide-react',
          ],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-utils': [
            'date-fns',
            'zod',
            'zustand',
            'axios',
            'react-hook-form',
            '@hookform/resolvers',
          ],
        },
      },
    },
  },
});
