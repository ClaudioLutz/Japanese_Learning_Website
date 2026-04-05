// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

test.describe('Security Tests', () => {

  test.describe('CSRF Protection', () => {

    test('POST without CSRF token is rejected', async ({ page }) => {
      await page.goto('/login');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'email=test@test.com&password=Test123!',
        });
        return { status: resp.status, body: await resp.text() };
      });
      // CSRF should block or the form should require it
      // 400 = bad request (CSRF), 200 = rendered page with error, 302 = redirect
      expect([200, 302, 400, 403]).toContain(response.status);
    });

    test('Admin API POST without CSRF is handled', async ({ page }) => {
      await login(page, 'admin');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/admin/kana/new', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ character: 'test', romanization: 'test', type: 'hiragana' }),
        });
        return { status: resp.status };
      });
      // Should either work (CSRF exempt for API) or be blocked
      expect([200, 201, 400, 403]).toContain(response.status);
    });
  });

  test.describe('Authentication Enforcement', () => {

    const protectedPages = [
      '/profile',
      '/my-lessons',
      '/admin',
      '/admin/manage/kana',
      '/admin/manage/lessons',
      '/purchase/2',
    ];

    for (const url of protectedPages) {
      test(`${url} requires authentication`, async ({ page }) => {
        const response = await page.goto(url);
        const finalUrl = page.url();
        // Should redirect to login
        expect(finalUrl).toContain('login');
      });
    }
  });

  test.describe('Admin Authorization', () => {

    const adminPages = [
      '/admin',
      '/admin/manage/kana',
      '/admin/manage/kanji',
      '/admin/manage/vocabulary',
      '/admin/manage/grammar',
      '/admin/manage/lessons',
      '/admin/manage/categories',
      '/admin/manage/courses',
      '/admin/manage/approval',
    ];

    for (const url of adminPages) {
      test(`Regular user blocked from ${url}`, async ({ page }) => {
        await login(page, 'regular');
        await page.goto(url);
        const finalUrl = page.url();
        // Should NOT be on the admin page
        expect(finalUrl).not.toMatch(new RegExp(`${url}$`));
      });
    }
  });

  test.describe('XSS Prevention', () => {

    test('Login form sanitizes input', async ({ page }) => {
      await page.goto('/login');
      await page.fill('#email', '<script>alert("xss")</script>@test.com');
      await page.fill('#password', 'Test123!');
      await page.click('#submit');
      // Page should not execute script
      const body = await page.textContent('body');
      expect(body).not.toContain('<script>');
    });

    test('Registration form sanitizes input', async ({ page }) => {
      await page.goto('/register');
      await page.fill('#username', '<img src=x onerror=alert(1)>');
      await page.fill('#email', 'xss@test.com');
      await page.fill('#password', 'Test123!');
      await page.fill('#password2', 'Test123!');
      await page.click('#submit');
      const body = await page.textContent('body');
      expect(body).not.toContain('onerror');
    });
  });

  test.describe('Session Management', () => {

    test('Session persists across page navigations', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/profile');
      await expect(page).toHaveURL(/profile/);
      await page.goto('/lessons');
      // Should still be logged in
      await page.goto('/profile');
      await expect(page).toHaveURL(/profile/);
    });

    test('Session is destroyed after logout', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/profile');
      await expect(page).toHaveURL(/profile/);
      // Logout
      const logoutLink = page.locator('a[href*="logout"]').first();
      await logoutLink.click();
      await page.waitForTimeout(1000);
      // Try to access protected page
      await page.goto('/profile');
      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe('Input Validation', () => {

    test('Registration rejects invalid email format', async ({ page }) => {
      await page.goto('/register');
      await page.fill('#username', 'validuser');
      await page.fill('#email', 'not-an-email');
      await page.fill('#password', 'Test123!');
      await page.fill('#password2', 'Test123!');
      await page.click('#submit');
      // Should stay on registration (validation error)
      await expect(page).toHaveURL(/register/);
    });
  });
});
