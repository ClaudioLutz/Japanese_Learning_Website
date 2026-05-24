// @ts-check
// E2E-Tests fuer die Kana-Uebung auf einem mobilen Touch-Geraet.
//
// Emuliert ein echtes Touch-Geraet (hasTouch + isMobile + Viewport via
// devices['iPhone 13']) — anders als ein blosser Viewport-Resize, der
// navigator.maxTouchPoints = 0 laesst.
//
// Voraussetzung (wie restliche Specs): laufender Test-Server + `npm install`.
// Der Test-User muss mind. eine Kana-Lesson abgeschlossen haben; ist nichts
// freigeschaltet (Seed-abhaengig), wird der Spiel-Teil sauber uebersprungen
// statt fehlzuschlagen.
const { test, expect, devices } = require('@playwright/test');
const { login } = require('./helpers');

test.use({ ...devices['iPhone 13'] });

test.describe('Kana-Uebung — Mobile / Touch', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'regular');
  });

  test('rendert auf Mobile ohne Alpine/Sortable-Konsolenfehler', async ({ page }) => {
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    await page.goto('/practice/kana');
    await expect(page.locator('.practice-kana-page')).toBeVisible();
    await page.waitForTimeout(800); // Alpine-Init + erste Session abwarten

    // Regressionsschutz fuer den x-for/SortableJS-Klon-Bug ("card is not defined").
    const cardErrors = errors.filter((e) => /card is not defined/i.test(e));
    expect(cardErrors, cardErrors.join('\n')).toHaveLength(0);
  });

  test('Bedien-Hilfe (Tap-to-Place) ist sichtbar', async ({ page }) => {
    await page.goto('/practice/kana');
    const pool = page.locator('.kana-grid-game__pool-card').first();
    if ((await pool.count()) === 0) {
      test.skip(true, 'Keine freigeschalteten Kana im Seed.');
    }
    await expect(page.locator('.kana-grid-game__taphint')).toContainText('antippen');
  });

  test('Pool ist auf Mobile ein sticky Tray', async ({ page }) => {
    await page.goto('/practice/kana');
    const pool = page.locator('.kana-grid-game__pool');
    if ((await page.locator('.kana-grid-game__pool-card').count()) === 0) {
      test.skip(true, 'Keine freigeschalteten Kana im Seed.');
    }
    const position = await pool.evaluate((el) => getComputedStyle(el).position);
    expect(position).toBe('sticky');
  });

  test('Tap-to-Place: Karte antippen → Feld antippen füllt das Feld korrekt', async ({ page }) => {
    await page.goto('/practice/kana');
    await page.waitForTimeout(500);

    const hasCards = (await page.locator('.kana-grid-game__pool-card').count()) > 0;
    if (!hasCards) {
      test.skip(true, 'Keine freigeschalteten Kana im Seed — Spiel nicht spielbar.');
    }

    // Ein noch leeres Feld und die dazu passende Pool-Karte ermitteln.
    const pair = await page.evaluate(() => {
      const cell = [...document.querySelectorAll('.kana-grid-game__cell')]
        .find((c) => !c.classList.contains('is-correct'));
      if (!cell) return null;
      const kanaId = cell.getAttribute('data-cell-id').replace('cell-', '');
      const card = document.querySelector(
        `.kana-grid-game__pool-card[data-kana-id="${kanaId}"]`
      );
      if (!card) return null;
      return { cellId: cell.getAttribute('data-cell-id'), token: card.getAttribute('data-token') };
    });
    expect(pair).not.toBeNull();

    // 1) Karte antippen → wird ausgewaehlt
    await page.tap(`.kana-grid-game__pool-card[data-token="${pair.token}"]`);
    await expect(
      page.locator(`.kana-grid-game__pool-card[data-token="${pair.token}"]`)
    ).toHaveClass(/is-selected/);

    // 2) Zielfeld antippen → wird korrekt befuellt
    await page.tap(`[data-cell-id="${pair.cellId}"]`);
    await expect(page.locator(`[data-cell-id="${pair.cellId}"]`)).toHaveClass(/is-correct/);

    // Auswahl ist danach wieder aufgehoben
    await expect(
      page.locator('.kana-grid-game__pool-card.is-selected')
    ).toHaveCount(0);
  });
});
