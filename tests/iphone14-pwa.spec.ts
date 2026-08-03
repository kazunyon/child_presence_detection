import { test, expect } from '@playwright/test';

test.describe('まもるバス iPhone 14相当 PWA確認', () => {
  test('トップ画面をiPhone 14相当で表示する', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/まもるバス/i);

    // iPhone 14相当の実画面キャプチャ
    await page.screenshot({
      path: 'screenshots/iphone14/01-top-screen.png',
      fullPage: true,
    });
  });

  test('モバイル画面の基本設定を確認する', async ({ page }) => {
    await page.goto('/');

    const environment = await page.evaluate(() => ({
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      touchPoints: navigator.maxTouchPoints,
      userAgent: navigator.userAgent,
      language: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }));

    console.log(environment);

    // モバイル幅であること
    expect(environment.viewportWidth).toBeLessThanOrEqual(430);

    // タッチ端末として認識されること
    expect(environment.touchPoints).toBeGreaterThan(0);

    // 日本語設定
    expect(environment.language).toBe('ja-JP');

    // JST設定
    expect(environment.timezone).toBe('Asia/Tokyo');
  });

  test('PWAマニフェストが設定されている', async ({ page }) => {
    await page.goto('/');

    const manifestHref = await page
      .locator('link[rel="manifest"]')
      .getAttribute('href');

    expect(manifestHref).toBeTruthy();

    const manifestResponse = await page.request.get(
      new URL(manifestHref!, page.url()).toString(),
    );

    expect(manifestResponse.ok()).toBeTruthy();

    const manifest = await manifestResponse.json();

    expect(manifest.name || manifest.short_name).toBeTruthy();

    console.log({
      name: manifest.name,
      shortName: manifest.short_name,
      display: manifest.display,
      startUrl: manifest.start_url,
    });
  });

  test('Service Workerが登録される', async ({ page }) => {
    await page.goto('/');

    // PWA登録処理を待つ
    await page.waitForTimeout(2_000);

    const registrations = await page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) {
        return [];
      }

      const items = await navigator.serviceWorker.getRegistrations();

      return items.map((registration) => ({
        scope: registration.scope,
        active: Boolean(registration.active),
        installing: Boolean(registration.installing),
        waiting: Boolean(registration.waiting),
      }));
    });

    console.log(registrations);

    expect(registrations.length).toBeGreaterThan(0);
  });

  test('位置情報を取得できる', async ({ page }) => {
    await page.goto('/');

    const position = await page.evaluate(
      () =>
        new Promise<{ latitude: number; longitude: number }>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              (result) => {
                resolve({
                  latitude: result.coords.latitude,
                  longitude: result.coords.longitude,
                });
              },
              reject,
              {
                enableHighAccuracy: true,
                timeout: 10_000,
              },
            );
          },
        ),
    );

    expect(position.latitude).toBeCloseTo(35.8617, 3);
    expect(position.longitude).toBeCloseTo(139.6455, 3);
  });
});