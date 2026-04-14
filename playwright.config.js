const { defineConfig } = require("@playwright/test");

const port = process.env.PLAYWRIGHT_BASE_PORT || "8503";
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`;

module.exports = defineConfig({
  testDir: "./tests/e2e",
  timeout: 180_000,
  expect: {
    timeout: 20_000,
  },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  outputDir: "output/playwright/test-results",
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "output/playwright/report" }],
  ],
  use: {
    baseURL,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 1100 },
  },
  webServer: {
    command: "python tests/e2e/run_app.py",
    env: {
      ...process.env,
      PLAYWRIGHT_BASE_PORT: port,
    },
    reuseExistingServer: !process.env.CI,
    timeout: 300_000,
    url: baseURL,
  },
});
