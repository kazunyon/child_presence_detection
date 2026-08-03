import { test, expect } from '@playwright/test';

test('まもるバスのトップ画面を表示できる', async ({ page }) => {
  await page.goto('http://localhost:5173');

  await expect(page).toHaveTitle(/まもるバス/i);

  await page.screenshot({
    path: 'test-results/mamoru-bus-home.png',
    fullPage: true,
  });
});
