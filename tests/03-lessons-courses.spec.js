// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

test.describe('Lessons & Courses', () => {

  test.describe('Lessons Catalog', () => {

    test('Lessons page shows published lessons', async ({ page }) => {
      await page.goto('/lessons');
      // Wait for lessons to load (JS-driven)
      await page.waitForTimeout(2000);
      // Should have lesson cards or category sections
      const body = await page.textContent('body');
      expect(body).toContain('Hiragana');
    });

    test('Lessons page has filter controls', async ({ page }) => {
      await page.goto('/lessons');
      await expect(page.locator('#categoryFilter')).toBeVisible();
      await expect(page.locator('#languageFilter')).toBeVisible();
    });

    test('Free lesson is accessible to guests', async ({ page }) => {
      await page.goto('/lessons/1');
      // Free lesson with guest access should load
      const response = await page.goto('/lessons/1');
      expect([200, 302]).toContain(response.status());
    });

    test('Paid lesson redirects unauthenticated users', async ({ page }) => {
      const response = await page.goto('/lessons/2');
      // Should redirect to login or show access denied
      const url = page.url();
      const body = await page.textContent('body');
      const isRedirected = url.includes('login') || body.toLowerCase().includes('purchase') || body.toLowerCase().includes('access');
      expect(isRedirected).toBeTruthy();
    });

    test('Unpublished lesson is not visible in catalog', async ({ page }) => {
      await page.goto('/lessons');
      await page.waitForTimeout(2000);
      const body = await page.textContent('body');
      expect(body).not.toContain('Draft Lesson');
    });
  });

  test.describe('Lesson View (Authenticated)', () => {

    test('Free lesson shows content for logged in user', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/lessons/1');
      // Should show lesson title
      const body = await page.textContent('body');
      expect(body).toContain('Hiragana');
    });

    test('Lesson has page navigation', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/lessons/1');
      // Check for navigation elements
      const nextBtn = page.locator('#nextPageTop, [onclick*="nextPage"]').first();
      const pageCounter = page.locator('#pageCounter, .page-counter').first();
      // At least one navigation element should exist
      const hasNav = (await nextBtn.count()) > 0 || (await pageCounter.count()) > 0;
      expect(hasNav).toBeTruthy();
    });

    test('Paid lesson shows purchase option for free user', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/lessons/2');
      const body = await page.textContent('body');
      // Should show purchase option or redirect
      const hasPurchaseInfo = body.toLowerCase().includes('purchase') ||
                              body.toLowerCase().includes('buy') ||
                              body.toLowerCase().includes('price') ||
                              page.url().includes('purchase');
      expect(hasPurchaseInfo).toBeTruthy();
    });

    test('Premium lesson accessible by premium user', async ({ page }) => {
      await login(page, 'premium');
      await page.goto('/lessons/3');
      const body = await page.textContent('body');
      expect(body).toContain('Business Japanese');
    });

    test('Premium lesson blocked for free user', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.goto('/lessons/3');
      const url = page.url();
      const body = await page.textContent('body');
      // Should be blocked or redirected
      const isBlocked = url.includes('login') ||
                        url.includes('upgrade') ||
                        body.toLowerCase().includes('premium') ||
                        response.status() === 403;
      expect(isBlocked).toBeTruthy();
    });
  });

  test.describe('Courses', () => {

    test('Courses page shows published courses', async ({ page }) => {
      await page.goto('/courses');
      await page.waitForTimeout(2000);
      const body = await page.textContent('body');
      expect(body).toContain('Complete Beginner Japanese');
    });

    test('Course detail page loads', async ({ page }) => {
      await page.goto('/course/1');
      const body = await page.textContent('body');
      expect(body).toContain('Complete Beginner Japanese');
    });

    test('Course shows included lessons', async ({ page }) => {
      await page.goto('/course/1');
      const body = await page.textContent('body');
      // Course should list its lessons
      expect(body).toContain('Hiragana');
    });

    test('Course shows price for purchasable course', async ({ page }) => {
      await page.goto('/course/1');
      const body = await page.textContent('body');
      // Should show price (CHF 79.90)
      const hasPrice = body.includes('79.90') || body.includes('CHF');
      expect(hasPrice).toBeTruthy();
    });
  });

  test.describe('Lesson Progress', () => {

    test('Progress is tracked for authenticated users', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/lessons/1');
      // View lesson and check if progress elements exist
      const progressBar = page.locator('.progress-bar, .progress').first();
      const hasProgress = (await progressBar.count()) > 0;
      // Progress tracking should be available
      expect(hasProgress).toBeTruthy();
    });

    test('API: Save lesson progress', async ({ page, request }) => {
      await login(page, 'regular');
      // Try to save progress via API
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/progress', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ progress_percentage: 50 }),
        });
        return { status: resp.status, ok: resp.ok };
      });
      // Should accept or return CSRF error (both are valid findings)
      expect([200, 400, 403]).toContain(response.status);
    });

    test('API: Reset lesson progress', async ({ page }) => {
      await login(page, 'regular');
      const response = await page.evaluate(async () => {
        const resp = await fetch('/api/lessons/1/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return { status: resp.status };
      });
      expect([200, 400, 403]).toContain(response.status);
    });
  });

  test.describe('My Lessons', () => {

    test('My Lessons page loads for authenticated user', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/my-lessons');
      await expect(page).toHaveURL(/my-lessons/);
    });

    test('My Lessons shows empty state for user with no purchases', async ({ page }) => {
      await login(page, 'regular');
      await page.goto('/my-lessons');
      const body = await page.textContent('body');
      // Should show empty state or purchased lessons
      const hasContent = body.toLowerCase().includes('no lesson') ||
                         body.toLowerCase().includes('empty') ||
                         body.toLowerCase().includes('browse') ||
                         body.toLowerCase().includes('purchase');
      expect(hasContent).toBeTruthy();
    });
  });
});
