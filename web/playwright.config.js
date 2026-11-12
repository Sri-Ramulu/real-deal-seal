// Browser tests for the main journeys, run against the real API in offline and simulated-checkout modes.
// npx playwright install chromium   (once), then: npm run e2e   — or set CHROME_PATH to use an installed Chrome.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  timeout: 30_000,
  workers: 1,
  use: {
    baseURL: 'http://localhost:8010',
    viewport: { width: 1440, height: 900 },
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH, args: ['--no-sandbox'] } : {},
  },
  webServer: {
    command: 'cd .. && rm -rf var-e2e && RDS_NO_DOTENV=1 RDS_REFRESH_HOURS=0 RDS_VAR_DIR=var-e2e RDS_PUBLIC_URL=http://localhost:8010 .venv/bin/uvicorn rds.main:app --app-dir api --port 8010',
    url: 'http://localhost:8010/api/health',
    timeout: 180_000,
    reuseExistingServer: false,
  },
});
