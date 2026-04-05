/**
 * Playwright Test Helpers - Authentication & Common Operations
 */

const BASE_URL = 'http://127.0.0.1:5000';

const TEST_USERS = {
  admin: { email: 'admin@test.com', password: 'Admin123!' },
  regular: { email: 'test@test.com', password: 'Test123!' },
  premium: { email: 'premium@test.com', password: 'Premium123!' },
};

/**
 * Login as a specific user
 */
async function login(page, userType = 'regular') {
  const user = TEST_USERS[userType];
  await page.goto('/login');
  await page.fill('#email', user.email);
  await page.fill('#password', user.password);
  await page.click('#submit');
  // Wait for redirect after login
  await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 10000 });
}

/**
 * Logout the current user
 */
async function logout(page) {
  // Find and click logout link/button
  const logoutLink = page.locator('a[href*="logout"]').first();
  if (await logoutLink.isVisible()) {
    await logoutLink.click();
    await page.waitForURL('**/login**', { timeout: 5000 }).catch(() => {});
  }
}

/**
 * Get CSRF token from the page
 */
async function getCsrfToken(page) {
  const token = await page.locator('input[name="csrf_token"]').first().getAttribute('value').catch(() => null);
  if (token) return token;
  // Try meta tag
  return await page.locator('meta[name="csrf-token"]').getAttribute('content').catch(() => '');
}

/**
 * Check if page has flash message
 */
async function hasFlashMessage(page, text) {
  const alert = page.locator('.alert');
  if (await alert.count() > 0) {
    const content = await alert.first().textContent();
    return content.includes(text);
  }
  return false;
}

/**
 * Wait for page to be fully loaded
 */
async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
}

module.exports = {
  BASE_URL,
  TEST_USERS,
  login,
  logout,
  getCsrfToken,
  hasFlashMessage,
  waitForPageLoad,
};
