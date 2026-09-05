const { defineConfig } = require('@playwright/test');
if (!process.env.E2E_BASE_URL) throw new Error('Use npm run test:e2e for isolated execution.');
module.exports = defineConfig({
  testDir: 'tests/e2e', timeout: 30_000, fullyParallel: false, workers: 1, reporter: 'line',
  use: { baseURL: process.env.E2E_BASE_URL, channel: 'chrome', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'tablet', use: { viewport: { width: 768, height: 1024 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 } } },
  ],
});
