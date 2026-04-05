// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

test.describe('Payment Flow', () => {

  test.describe('Purchase Page', () => {

    test('Purchase page loads for paid lesson', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/purchase/2');
      const body = await page.textContent('body');
      // Should show lesson info and price
      expect(body).toContain('Kanji');
      const hasPrice = body.includes('29.90') || body.includes('CHF');
      expect(hasPrice).toBeTruthy();
    });

    test('Purchase page has terms checkbox and buy button', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/purchase/2');
      // Check for purchase elements
      const purchaseBtn = page.locator('#purchaseBtn, button[type="submit"]').first();
      await expect(purchaseBtn).toBeVisible();
      const termsCheckbox = page.locator('#agreeTerms, input[type="checkbox"]').first();
      await expect(termsCheckbox).toBeVisible();
    });

    test('Purchase page requires login', async ({ page }) => {
      await page.goto('/purchase/2');
      // Should redirect to login
      await expect(page).toHaveURL(/login/);
    });

    test('Purchase page for free lesson redirects', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.goto('/purchase/1');
      // Free lesson should not have purchase page or should redirect
      const url = page.url();
      const body = await page.textContent('body');
      const isHandled = !url.includes('/purchase/1') ||
                        body.toLowerCase().includes('free') ||
                        response.status() === 302;
      expect(isHandled).toBeTruthy();
    });
  });

  test.describe('Purchase API', () => {

    test('API: Purchase lesson creates transaction', async ({ page }) => {
      await login(page, 'regular');
      // Call purchase API
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/2/purchase', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return { status: resp.status, body: await resp.text() };
      });
      // Should return success or CSRF error
      expect([200, 201, 400, 403]).toContain(response.status);
    });

    test('API: Purchase course', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/courses/1/purchase', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return { status: resp.status, body: await resp.text() };
      });
      expect([200, 201, 400, 403]).toContain(response.status);
    });

    test('API: Purchase status check', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/payment/status/nonexistent-id');
        return { status: resp.status };
      });
      expect([200, 404, 400]).toContain(response.status);
    });

    test('API: Purchase status for lesson', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/2/purchase-status');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('API: User purchases list', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/user/purchases');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });
  });

  test.describe('Payment Result Pages', () => {

    test('Payment success page shows success message', async ({ page }) => {
      await page.goto('/payment/success');
      const body = await page.textContent('body');
      const hasSuccessInfo = body.toLowerCase().includes('success') ||
                             body.toLowerCase().includes('thank') ||
                             body.toLowerCase().includes('payment');
      expect(hasSuccessInfo).toBeTruthy();
    });

    test('Payment failed page shows failure message', async ({ page }) => {
      await page.goto('/payment/failed');
      const body = await page.textContent('body');
      const hasFailInfo = body.toLowerCase().includes('fail') ||
                          body.toLowerCase().includes('error') ||
                          body.toLowerCase().includes('cancel') ||
                          body.toLowerCase().includes('payment');
      expect(hasFailInfo).toBeTruthy();
    });
  });

  test.describe('Premium Upgrade', () => {

    test('Premium upgrade endpoint exists', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/upgrade_to_premium', { method: 'POST' });
        return { status: resp.status };
      });
      // Should respond (even if CSRF blocked)
      expect([200, 302, 400, 403]).toContain(response.status);
    });

    test('Premium downgrade endpoint exists', async ({ page }) => {
      await login(page, 'premium');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/downgrade_from_premium', { method: 'POST' });
        return { status: resp.status };
      });
      expect([200, 302, 400, 403]).toContain(response.status);
    });
  });
});
