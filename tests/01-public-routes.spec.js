// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Public Routes', () => {

  test('GET / - Homepage loads with language selection', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await expect(page).toHaveTitle(/Japanese/i);
    // Language cards should be visible
    await expect(page.locator('.language-card').first()).toBeVisible();
    const cardCount = await page.locator('.language-card').count();
    expect(cardCount).toBe(2);
  });

  test('GET /home - Same as homepage', async ({ page }) => {
    await page.goto('/home');
    await expect(page.locator('.language-card')).toHaveCount(2);
  });

  test('GET /healthz - Returns OK', async ({ page }) => {
    const response = await page.goto('/healthz');
    expect(response.status()).toBe(200);
  });

  test('GET /health - Returns health check info', async ({ page }) => {
    const response = await page.goto('/health');
    expect(response.status()).toBe(200);
  });

  test('GET /lessons - Lessons catalog loads', async ({ page }) => {
    await page.goto('/lessons');
    await expect(page).toHaveTitle(/Lesson/i);
    // Filter controls should exist
    await expect(page.locator('#categoryFilter')).toBeVisible();
    await expect(page.locator('#languageFilter')).toBeVisible();
  });

  test('GET /courses - Courses page loads', async ({ page }) => {
    await page.goto('/courses');
    await page.waitForLoadState('domcontentloaded');
    await expect(page).toHaveTitle(/Course/i);
  });

  test('GET /login - Login page loads with form', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#submit')).toBeVisible();
  });

  test('GET /register - Registration page loads with form', async ({ page }) => {
    await page.goto('/register', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#password2')).toBeVisible();
    await expect(page.locator('#submit')).toBeVisible();
  });

  test('GET /profile - Redirects to login for unauthenticated users', async ({ page }) => {
    await page.goto('/profile');
    await expect(page).toHaveURL(/login/);
  });

  test('GET /my-lessons - Redirects to login for unauthenticated users', async ({ page }) => {
    await page.goto('/my-lessons');
    await expect(page).toHaveURL(/login/);
  });

  test('GET /admin - Redirects to login for unauthenticated users', async ({ page }) => {
    await page.goto('/admin');
    await expect(page).toHaveURL(/login/);
  });

  test('GET /nonexistent - Returns 404', async ({ page }) => {
    const response = await page.goto('/nonexistent');
    expect(response.status()).toBe(404);
  });

  test('Navigation bar has correct links for guests', async ({ page }) => {
    await page.goto('/');
    // Guests should see login and register
    await expect(page.locator('a[href*="login"]').first()).toBeVisible();
    await expect(page.locator('a[href*="register"]').first()).toBeVisible();
  });

  test('Homepage language selection works', async ({ page }) => {
    await page.goto('/');
    // Click English language card
    const englishCard = page.locator('.language-card').first();
    await englishCard.click();
    // Should navigate to lessons with language filter
    await page.waitForTimeout(1000);
  });

  test('GET /payment/success - Payment success page loads', async ({ page }) => {
    const response = await page.goto('/payment/success');
    // Should load even without a real transaction
    expect([200, 302]).toContain(response.status());
  });

  test('GET /payment/failed - Payment failed page loads', async ({ page }) => {
    const response = await page.goto('/payment/failed');
    expect([200, 302]).toContain(response.status());
  });

  test('API /api/categories - Returns categories JSON', async ({ page }) => {
    const response = await page.goto('/api/categories');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
    expect(body.length).toBeGreaterThanOrEqual(3);
  });

  test('API /api/courses - Returns courses JSON', async ({ page }) => {
    const response = await page.goto('/api/courses');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
  });
});
