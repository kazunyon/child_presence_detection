import { test, expect } from '@playwright/test';

test.use({
  locale: 'ja-JP',
  timezoneId: 'Asia/Tokyo',
  viewport: {
    height: 844,
    width: 390
  }
});

test('test', async ({ page }) => {
  await page.goto('https://kazunyon.github.io/child_presence_detection/');
  await page.getByRole('textbox', { name: '職員ID' }).click();
  await page.getByRole('textbox', { name: '職員ID' }).fill('1');
  await page.getByRole('textbox', { name: '職員ID' }).press('Tab');
  await page.getByRole('textbox', { name: 'PIN' }).fill('1234');
  await page.getByRole('button', { name: 'ログイン' }).click();
  await page.getByRole('button', { name: '運行画面を開く' }).click();
  await page.getByRole('button', { name: 'バスを選び直す' }).click();
  await page.getByRole('button', { name: '中止して選び直す' }).click();
  await page.getByRole('button', { name: '中止して選び直す' }).click();
  await page.getByRole('button', { name: 'バスを選び直す' }).click();
  await page.getByRole('button', { name: '中止して選び直す' }).click();
  await page.getByRole('button', { name: '一時保存してホームへ戻る' }).click();
  await page.getByRole('button', { name: '🚌 運行' }).click();
  await page.getByRole('button', { name: '⌂ ホーム' }).click();
  await page.getByRole('button', { name: '🚌 運行' }).click();
  await page.getByRole('button', { name: '⌂ ホーム' }).click();
});