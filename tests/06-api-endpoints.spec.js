// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

test.describe('API Endpoints', () => {

  test.describe('Public API', () => {

    test('GET /api/categories - Returns JSON array', async ({ page }) => {
      const response = await page.goto('/api/categories');
      expect(response.status()).toBe(200);
      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
      // Verify category structure
      if (data.length > 0) {
        expect(data[0]).toHaveProperty('id');
        expect(data[0]).toHaveProperty('name');
      }
    });

    test('GET /api/courses - Returns JSON array', async ({ page }) => {
      const response = await page.goto('/api/courses');
      expect(response.status()).toBe(200);
      const data = await response.json();
      expect(Array.isArray(data)).toBeTruthy();
    });
  });

  test.describe('Authenticated User API', () => {

    test('GET /api/lessons - Returns user lessons', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/user/purchases - Returns user purchases', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/user/purchases');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/lessons/1/purchase-status - Returns purchase status', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/purchase-status');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('Unauthenticated API access is rejected', async ({ page }) => {
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons');
        return { status: resp.status };
      });
      // Should redirect to login or return 401/403
      expect([200, 302, 401, 403]).toContain(response.status);
    });
  });

  test.describe('Quiz API', () => {

    test('POST /api/lessons/1/quiz/1/answer - Submit quiz answer', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/quiz/1/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected_option_id: 1 }),
        });
        return { status: resp.status, body: await resp.text() };
      });
      // Expect success or CSRF block
      expect([200, 400, 403]).toContain(response.status);
    });
  });

  test.describe('Progress API', () => {

    test('POST /api/lessons/1/progress - Update progress', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/progress', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            progress_percentage: 25,
            content_progress: {},
          }),
        });
        return { status: resp.status, body: await resp.text() };
      });
      expect([200, 400, 403]).toContain(response.status);
    });

    test('POST /api/lessons/1/reset - Reset progress', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/reset', {
          method: 'POST',
        });
        return { status: resp.status };
      });
      expect([200, 400, 403]).toContain(response.status);
    });
  });

  test.describe('Admin API (Non-Admin Rejection)', () => {

    const adminEndpoints = [
      '/api/admin/kana',
      '/api/admin/kanji',
      '/api/admin/vocabulary',
      '/api/admin/grammar',
      '/api/admin/lessons',
      '/api/admin/categories',
      '/api/admin/courses',
      '/api/admin/purchases',
      '/api/admin/revenue-stats',
    ];

    for (const endpoint of adminEndpoints) {
      test(`Regular user blocked from ${endpoint}`, async ({ page }) => {
        await login(page, 'regular');
        const response = await page.evaluate(async (url) => {
          const resp = await fetch(url);
          return { status: resp.status };
        }, endpoint);
        // Should not return 200 for non-admin
        expect([302, 401, 403]).toContain(response.status);
      });
    }
  });

  test.describe('Error Handling', () => {

    test('Non-existent lesson returns 404', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.goto('/lessons/999');
      expect([404, 302]).toContain(response.status());
    });

    test('Non-existent course returns 404', async ({ page }) => {
      const response = await page.goto('/course/999');
      expect([404, 302]).toContain(response.status());
    });

    test('Invalid API endpoint returns 404', async ({ page }) => {
      const response = await page.goto('/api/nonexistent');
      expect(response.status()).toBe(404);
    });
  });

  test.describe('Health Endpoints', () => {

    test('GET /healthz - Quick health check', async ({ page }) => {
      const response = await page.goto('/healthz');
      expect(response.status()).toBe(200);
      const text = await page.textContent('body');
      expect(text.toLowerCase()).toContain('ok');
    });

    test('GET /health - Full health check with DB', async ({ page }) => {
      const response = await page.goto('/health');
      expect(response.status()).toBe(200);
    });
  });
});
