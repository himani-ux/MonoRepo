// playwright.config.mjs — journey-spec execution config (Increment 2).
// The spec directory and app URL come from the environment so the same
// config serves the fixture-app acceptance loop and consuming projects.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: process.env.JOURNEY_TESTS_DIR || '../../tests/journeys',
  use: { baseURL: process.env.APP_BASE_URL || 'http://localhost:4173' },
  reporter: [['list']],
  workers: 1,
});
