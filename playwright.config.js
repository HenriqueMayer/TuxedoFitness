const { defineConfig } = require('@playwright/test');
const os = require('os');
const path = require('path');

const e2eDatabase = process.env.TUXEDO_FITNESS_DB
  || path.join(os.tmpdir(), `tuxedo-fitness-e2e-${process.pid}.sqlite3`);

module.exports = defineConfig({
  testDir: 'tests/e2e',
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:8010',
    channel: 'chrome',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'tablet', use: { viewport: { width: 768, height: 1024 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 } } },
  ],
  webServer: {
    command: 'sh scripts/run-e2e-server.sh',
    url: 'http://127.0.0.1:8010/health/',
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      SECRET_KEY: 'synthetic-e2e-django-key',
      DEBUG: 'False',
      ALLOWED_HOSTS: '127.0.0.1,localhost',
      TUXEDO_FITNESS_DB: e2eDatabase,
      UV_CACHE_DIR: '/tmp/tuxedo-fitness-uv-cache',
    },
  },
});
