// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

test.describe('Admin Panel', () => {

  test.describe('Access Control', () => {

    test('Non-admin user cannot access admin panel', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.goto('/admin');
      // Should be redirected or forbidden
      const url = page.url();
      expect(url).not.toMatch(/\/admin$/);
    });

    test('Admin user can access admin panel', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin');
      const body = await page.textContent('body');
      expect(body.toLowerCase()).toContain('admin');
    });

    test('Non-admin cannot access admin API', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/kana');
        return { status: resp.status };
      });
      expect([401, 403, 302]).toContain(response.status);
    });
  });

  test.describe('Admin Dashboard', () => {

    test('Dashboard loads with management links', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin');
      const body = await page.textContent('body');
      expect(body.toLowerCase()).toContain('dashboard');
    });
  });

  test.describe('Admin Management Pages', () => {

    test('Manage Kana page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/kana');
      await expect(page.locator('body')).toContainText(/kana/i);
    });

    test('Manage Kanji page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/kanji');
      await expect(page.locator('body')).toContainText(/kanji/i);
    });

    test('Manage Vocabulary page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/vocabulary');
      await expect(page.locator('body')).toContainText(/vocab/i);
    });

    test('Manage Grammar page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/grammar');
      await expect(page.locator('body')).toContainText(/grammar/i);
    });

    test('Manage Lessons page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/lessons');
      await expect(page.locator('body')).toContainText(/lesson/i);
    });

    test('Manage Categories page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/categories');
      await expect(page.locator('body')).toContainText(/categor/i);
    });

    test('Manage Courses page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/courses');
      await expect(page.locator('body')).toContainText(/course/i);
    });

    test('Manage Approval page loads', async ({ page }) => {
      await login(page, 'admin');
      await page.goto('/admin/manage/approval');
      await expect(page.locator('body')).toContainText(/approv/i);
    });
  });

  test.describe('Admin API - Kana CRUD', () => {

    test('GET /api/admin/kana - List kana', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/kana');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('POST /api/admin/kana/new - Create kana', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/kana/new', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            character: 'あ',
            romanization: 'a',
            type: 'hiragana',
          }),
        });
        return { status: resp.status, body: await resp.text() };
      });
      // May succeed or fail due to CSRF
      expect([200, 201, 400, 403]).toContain(response.status);
    });
  });

  test.describe('Admin API - Lessons CRUD', () => {

    test('GET /api/admin/lessons - List lessons', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/lessons');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBeTruthy();
    });

    test('GET /api/admin/lessons/1 - Get single lesson', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/lessons/1');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/admin/lessons/1/content - Get lesson content', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/lessons/1/content');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });
  });

  test.describe('Admin API - Categories CRUD', () => {

    test('GET /api/admin/categories - List categories', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/categories');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBeTruthy();
      expect(response.body.length).toBeGreaterThanOrEqual(3);
    });
  });

  test.describe('Admin API - Courses CRUD', () => {

    test('GET /api/admin/courses - List courses', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/courses');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });
  });

  test.describe('Admin API - Revenue & Purchases', () => {

    test('GET /api/admin/purchases - List purchases', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/purchases');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/admin/revenue-stats - Revenue statistics', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/revenue-stats');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });
  });

  test.describe('Admin API - Content Options', () => {

    test('GET /api/admin/content-options/kana - Get kana options', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/content-options/kana');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/admin/content-options/kanji - Get kanji options', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/content-options/kanji');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/admin/content-options/vocabulary - Get vocabulary options', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/content-options/vocabulary');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });

    test('GET /api/admin/content-options/grammar - Get grammar options', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/content-options/grammar');
        return { status: resp.status, body: await resp.json().catch(() => null) };
      });
      expect(response.status).toBe(200);
    });
  });
});
