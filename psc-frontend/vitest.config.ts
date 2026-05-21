import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts', './tests/frontend/safety/setup.ts'],
    include: [
      'src/**/*.test.ts',
      'src/**/*.test.tsx',
      'src/**/*.spec.ts',
      'src/**/*.spec.tsx',
      'tests/frontend/**/*.test.ts',
      'tests/frontend/**/*.test.tsx',
      'tests/frontend/**/*.spec.ts',
      'tests/frontend/**/*.spec.tsx',
    ],
    clearMocks: true,
    restoreMocks: true,
  },
});

