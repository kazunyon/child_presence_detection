import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',

  // 各テストを独立して実行
  fullyParallel: true,

  // テスト失敗時の調査用
  retries: 0,

  reporter: [
    ['html', { open: 'never' }],
  ],

  use: {
    // まもるバスのローカルURL
    baseURL: 'http://localhost:5173',

    // 日本向け設定
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo',

    // テスト失敗時に記録
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      // Windows PC通常画面
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },

    {
      // Windows上でiPhone 14相当を再現
      name: 'iphone-14-chromium-pwa',
      use: {
        ...devices['iPhone 14'],

        // iPhone設定を使いつつ、実行エンジンはChromium
        browserName: 'chromium',

        // さいたま市付近のテスト位置
        geolocation: {
          latitude: 35.8617,
          longitude: 139.6455,
        },

        permissions: [
          'geolocation',
          'notifications',
        ],

        // PWAの外観確認
        colorScheme: 'light',
      },
    },
  ],

  // ViteをPlaywrightから自動起動する場合
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 120_000,
  },
});