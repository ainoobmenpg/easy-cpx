import { test, expect } from '@playwright/test';

test.describe('UI smoke', () => {
  test('home loads', async ({ page, baseURL }) => {
    await page.goto(baseURL!);
    await expect(page).toHaveTitle(/作戦級CPX|Operational CPX/i);
  });

  test('scenarios -> start game -> game page', async ({ page, baseURL }) => {
    // Move to scenarios
    await page.goto(`${baseURL}/scenarios`);
    // Wait for scenario cards
    await page.waitForSelector('div[role="main"] >> text=Map:', { timeout: 10000 }).catch(() => {});

    // Fallback: pick first card by container style
    const cards = page.locator('main .grid > div');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
    await cards.first().click();

    // Modal appears with start button
    const startButton = page.getByRole('button', { name: /開始|ミッション開始/ });
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Navigates to /game?gameId=*
    await page.waitForURL(/\/game\?gameId=\d+/, { timeout: 15000 });

    // Basic HUD elements
    await expect(page.locator('header')).toContainText(/作戦級CPX/);
    await expect(page.locator('text=T')).toBeVisible(); // Turn indicator hint
  });
});

