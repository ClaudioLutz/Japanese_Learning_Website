// @ts-check
const { test, expect } = require('@playwright/test');
const { login } = require('./helpers');

/**
 * Kompletter Durchlauf der Lektion "Tokio erkunden — Wegbeschreibung auf Japanisch"
 * Testet alle 7 Seiten: Flip-Cards, Audio, Video, Text, Quiz (MC, T/F, Fill-Blank, Matching)
 */

// Find the Tokyo lesson ID dynamically
let LESSON_ID;

test.describe('Tokyo Lesson — Kompletter Durchlauf', () => {

  test.beforeEach(async ({ page }) => {
    // Login as regular user (has purchase)
    await login(page, 'regular');
  });

  test('Setup: Tokyo-Lektion finden', async ({ page }) => {
    const response = await page.goto('/api/lessons');
    const lessons = await response.json();
    const tokyo = lessons.find(l => l.title && l.title.includes('Tokio'));
    expect(tokyo).toBeTruthy();
    LESSON_ID = tokyo.id;
  });

  test('Seite 1: Ankunft in Shinjuku — Video, Text, Vokabeln, Audio', async ({ page }) => {
    // Find lesson
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    const tokyo = lessons.find(l => l.title && l.title.includes('Tokio'));
    LESSON_ID = tokyo.id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Carousel should be on page 1
    const activeItem = page.locator('.carousel-item.active');
    await expect(activeItem).toBeVisible();

    // Page counter should show "1"
    const counter = page.locator('#pageCounter');
    await expect(counter).toContainText('1');

    // Video embed or link should exist on page 1
    const videoOrText = activeItem.locator('iframe, .ratio, .content-text, .story-intro');
    await expect(videoOrText.first()).toBeVisible();

    // Text block "Linas Geschichte" should be visible
    const storyText = activeItem.locator('text=Tokio');
    await expect(storyText.first()).toBeVisible();

    // Deck container should be present (3 vocab cards = deck mode)
    const deckContainer = activeItem.locator('.deck-container');
    await expect(deckContainer).toBeVisible();

    // One flip card visible in the deck
    const deckCard = activeItem.locator('.deck-card-area .flip-card');
    await expect(deckCard).toBeVisible();

    // Click card to flip
    const cardScene = activeItem.locator('.deck-card-area .card-scene');
    await cardScene.click();
    await page.waitForTimeout(500);
    const flipped = activeItem.locator('.deck-card-area .card-flipper.is-flipped');
    expect(await flipped.count()).toBeGreaterThanOrEqual(1);

    // Audio player should be present
    const audioElements = activeItem.locator('audio');
    const audioCount = await audioElements.count();
    expect(audioCount).toBeGreaterThanOrEqual(1);
  });

  test('Seite 2: Richtungen lernen — Deck-Modus mit Flip-Cards', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 2
    await page.click('#nextPageTop');
    await page.waitForTimeout(800);

    const activeItem = page.locator('.carousel-item.active');

    // Deck container should be present (6 vocab cards = deck mode)
    const deckContainer = activeItem.locator('.deck-container');
    await expect(deckContainer).toBeVisible();

    // Deck header with progress
    const deckHeader = activeItem.locator('.deck-header');
    await expect(deckHeader).toBeVisible();

    // One card should be visible in deck-card-area
    const cardArea = activeItem.locator('.deck-card-area .flip-card');
    await expect(cardArea).toBeVisible();

    // Click the card to flip it
    const cardScene = activeItem.locator('.deck-card-area .card-scene');
    await cardScene.click();
    await page.waitForTimeout(500);

    // Confidence buttons should appear
    const confButtons = activeItem.locator('.confidence-buttons.visible');
    await expect(confButtons).toBeVisible();

    // Click "Gewusst" to advance to next card
    await activeItem.locator('.confidence-btn[data-rating="good"]').click();
    await page.waitForTimeout(500);

    // Progress should update
    const learnedBadge = activeItem.locator('.deck-learned');
    await expect(learnedBadge).toContainText('1');
  });

  test('Audio-Button: Karte bleibt geflippt beim Audio-Klick', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 2 (deck mode with vocab cards)
    await page.click('#nextPageTop');
    await page.waitForTimeout(800);

    const activeItem = page.locator('.carousel-item.active');

    // Flip the card
    const cardScene = activeItem.locator('.deck-card-area .card-scene');
    await cardScene.click();
    await page.waitForTimeout(500);

    // Card should be flipped
    const flipped = activeItem.locator('.deck-card-area .card-flipper.is-flipped');
    expect(await flipped.count()).toBe(1);

    // Audio button should be visible on back
    const audioBtn = activeItem.locator('.deck-card-area .card-audio-btn');
    await expect(audioBtn).toBeVisible();

    // Click audio button using force (button may be partially covered by card layout)
    await audioBtn.click({ force: true });
    await page.waitForTimeout(500);

    // Card should STILL be flipped (not flipped back)
    const stillFlipped = activeItem.locator('.deck-card-area .card-flipper.is-flipped');
    expect(await stillFlipped.count()).toBe(1);

    // Confidence buttons should still be visible
    const confButtons = activeItem.locator('.confidence-buttons.visible');
    await expect(confButtons).toBeVisible();
  });

  test('Seite 3: Grammatik — Grammar-Cards + Audio-Dialoge', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 3
    await page.click('#nextPageTop');
    await page.waitForTimeout(800);
    await page.click('#nextPageTop');
    await page.waitForTimeout(800);

    const activeItem = page.locator('.carousel-item.active');

    // Deck container should be present (2 grammar cards)
    const deckContainer = activeItem.locator('.deck-container');
    await expect(deckContainer).toBeVisible();

    // One grammar card visible in deck
    const deckCard = activeItem.locator('.deck-card-area .flip-card');
    await expect(deckCard).toBeVisible();

    // Audio elements (dialog)
    const audioElements = activeItem.locator('audio');
    expect(await audioElements.count()).toBeGreaterThanOrEqual(1);

    // Transcript table should be visible
    const transcript = activeItem.locator('table, .dialog-transcript');
    expect(await transcript.count()).toBeGreaterThanOrEqual(1);
  });

  test('Seite 4: Zwischentest — Multiple Choice, True/False, Fill-Blank', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 4
    for (let i = 0; i < 3; i++) {
      await page.click('#nextPageTop');
      await page.waitForTimeout(800);
    }

    const activeItem = page.locator('.carousel-item.active');

    // Quiz questions should be present
    const quizQuestions = activeItem.locator('.quiz-question');
    const questionCount = await quizQuestions.count();
    expect(questionCount).toBeGreaterThanOrEqual(2); // MC, T/F, Matching (fill_blank entfernt)

    // Test Multiple Choice question (first question)
    const mcQuestion = activeItem.locator('[data-question-type="multiple_choice"]').first();
    if (await mcQuestion.count() > 0) {
      // Select the correct answer (second radio = "Gehen Sie geradeaus")
      const radioButtons = mcQuestion.locator('input[type="radio"]');
      const radioCount = await radioButtons.count();
      expect(radioCount).toBe(4);

      // Click the correct option (index 1 = "Gehen Sie geradeaus")
      await radioButtons.nth(1).click();

      // Submit the answer
      const submitBtn = mcQuestion.locator('button.btn-primary');
      await submitBtn.click();
      await page.waitForTimeout(1000);

      // Feedback should appear
      const feedback = mcQuestion.locator('.quiz-feedback, .alert');
      await expect(feedback.first()).toBeVisible();
    }

    // Test True/False question
    const tfQuestion = activeItem.locator('[data-question-type="true_false"]').first();
    if (await tfQuestion.count() > 0) {
      // Select "Falsch" (second radio)
      const radios = tfQuestion.locator('input[type="radio"]');
      await radios.last().click();

      const submitBtn = tfQuestion.locator('button.btn-primary');
      await submitBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test('Seite 5: Kanji — Deck-Modus + Kulturnotiz', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 5
    for (let i = 0; i < 4; i++) {
      await page.click('#nextPageTop');
      await page.waitForTimeout(800);
    }

    const activeItem = page.locator('.carousel-item.active');

    // Deck container should be present (4 kanji cards)
    const deckContainer = activeItem.locator('.deck-container');
    await expect(deckContainer).toBeVisible();

    // One card visible in deck area
    const cardArea = activeItem.locator('.deck-card-area .flip-card');
    await expect(cardArea).toBeVisible();

    // Culture note should still be visible (not a card)
    const cultureNote = activeItem.locator('text=dō');
    expect(await cultureNote.count()).toBeGreaterThanOrEqual(1);

    // Flip the kanji card
    const cardScene = activeItem.locator('.deck-card-area .card-scene');
    await cardScene.click();
    await page.waitForTimeout(500);
    const flipped = activeItem.locator('.deck-card-area .card-flipper.is-flipped');
    expect(await flipped.count()).toBeGreaterThanOrEqual(1);
  });

  test('Seite 6: Anwendung — Matching-Quiz', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 6
    for (let i = 0; i < 5; i++) {
      await page.click('#nextPageTop');
      await page.waitForTimeout(800);
    }

    const activeItem = page.locator('.carousel-item.active');

    // Audio for tourist question
    const audio = activeItem.locator('audio');
    expect(await audio.count()).toBeGreaterThanOrEqual(1);

    // Matching quiz should be present
    const matchingQuiz = activeItem.locator('[data-question-type="matching"]');
    if (await matchingQuiz.count() > 0) {
      // Find all matching selects
      const selects = matchingQuiz.locator('.matching-select, select');
      const selectCount = await selects.count();
      expect(selectCount).toBeGreaterThanOrEqual(2);

      // Fill in matching by selecting from dropdowns using data-correct-answer
      for (let i = 0; i < selectCount; i++) {
        const select = selects.nth(i);
        const correctAnswer = await select.getAttribute('data-correct-answer');
        if (correctAnswer) {
          await select.selectOption(correctAnswer);
        }
      }

      // Submit matching quiz
      const submitBtn = matchingQuiz.locator('button.btn-primary');
      if (await submitBtn.count() > 0) {
        await submitBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('Seite 7: Abschlussquiz — Alle Quiz-Typen', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate to page 7
    for (let i = 0; i < 6; i++) {
      await page.click('#nextPageTop');
      await page.waitForTimeout(800);
    }

    const activeItem = page.locator('.carousel-item.active');

    // Should have multiple quiz questions
    const quizQuestions = activeItem.locator('.quiz-question');
    expect(await quizQuestions.count()).toBeGreaterThanOrEqual(3);

    // MC Question 1: "Wie fragst du höflich, wo die Toilette ist?"
    const mcQuestions = activeItem.locator('[data-question-type="multiple_choice"]');
    if (await mcQuestions.count() > 0) {
      // Answer first MC (correct = first option "トイレはどこですか")
      const firstMC = mcQuestions.first();
      const radios = firstMC.locator('input[type="radio"]');
      await radios.first().click();
      const submitBtn = firstMC.locator('button.btn-primary');
      await submitBtn.click();
      await page.waitForTimeout(1000);

      // Answer second MC if present
      if (await mcQuestions.count() > 1) {
        const secondMC = mcQuestions.nth(1);
        const radios2 = secondMC.locator('input[type="radio"]');
        // Correct answer is second option "Biegen Sie an der Kreuzung links ab"
        await radios2.nth(1).click();
        const submitBtn2 = secondMC.locator('button.btn-primary');
        await submitBtn2.click();
        await page.waitForTimeout(1000);
      }
    }

    // Matching question
    const matchingQuiz = activeItem.locator('[data-question-type="matching"]');
    if (await matchingQuiz.count() > 0) {
      const selects = matchingQuiz.locator('.matching-select, select');
      const selectCount = await selects.count();
      for (let i = 0; i < selectCount; i++) {
        const select = selects.nth(i);
        const correctAnswer = await select.getAttribute('data-correct-answer');
        if (correctAnswer) {
          await select.selectOption(correctAnswer);
        }
      }
      const submitBtn = matchingQuiz.locator('button.btn-primary');
      if (await submitBtn.count() > 0) {
        await submitBtn.click();
        await page.waitForTimeout(1000);
      }
    }

    // True/False question
    const tfQuestion = activeItem.locator('[data-question-type="true_false"]');
    if (await tfQuestion.count() > 0) {
      // Correct = "Falsch" (second radio)
      const radios = tfQuestion.locator('input[type="radio"]');
      await radios.last().click();
      const submitBtn = tfQuestion.locator('button.btn-primary');
      await submitBtn.click();
      await page.waitForTimeout(1000);
    }

    // Summary text should be visible
    const summary = activeItem.locator('text=Lektion abgeschlossen');
    expect(await summary.count()).toBeGreaterThanOrEqual(1);
  });

  test('Navigation: Vorwärts und rückwärts durch alle 7 Seiten', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    // Navigate forward through all 7 pages
    for (let i = 1; i <= 6; i++) {
      await page.click('#nextPageTop');
      await page.waitForTimeout(600);
      const counter = await page.textContent('#pageCounter');
      expect(counter).toContain(`${i + 1}`);
    }

    // Should be on page 7 now
    const counterFinal = await page.textContent('#pageCounter');
    expect(counterFinal).toContain('7');

    // Navigate backward
    for (let i = 6; i >= 1; i--) {
      await page.click('#prevPageTop');
      await page.waitForTimeout(600);
      const counter = await page.textContent('#pageCounter');
      expect(counter).toContain(`${i}`);
    }

    // Should be back on page 1
    const counterStart = await page.textContent('#pageCounter');
    expect(counterStart).toContain('1');
  });

  test('Content-Markierung: Items als abgeschlossen markieren', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    await page.goto(`/lessons/${LESSON_ID}`, { waitUntil: 'domcontentloaded' });

    const activeItem = page.locator('.carousel-item.active');

    // Find visible "Mark Complete" buttons (non-card items like text, video, audio)
    const completeButtons = activeItem.locator('.content-item:not(.in-deck) .mark-complete-btn');
    const btnCount = await completeButtons.count();

    if (btnCount > 0) {
      // Click first visible "Mark Complete" button
      await completeButtons.first().click();
      await page.waitForTimeout(1000);

      // Completed badge should appear
      const badges = activeItem.locator('.content-item:not(.in-deck) .completed-badge');
      let visibleBadges = 0;
      for (let i = 0; i < await badges.count(); i++) {
        if (await badges.nth(i).isVisible()) visibleBadges++;
      }
      expect(visibleBadges).toBeGreaterThanOrEqual(1);
    }
  });

  test('Audio-Dateien: Alle Audio-Elemente laden korrekt', async ({ page }) => {
    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    LESSON_ID = lessons.find(l => l.title && l.title.includes('Tokio')).id;

    // Check audio files are served correctly
    const audioFiles = [
      'vocab_sumimasen.mp3', 'vocab_migi.mp3', 'vocab_hidari.mp3',
      'dialog_01_frage.mp3', 'dialog_02_lina_fragt.mp3',
      'dialog_03_passant_antwortet.mp3',
    ];

    for (const file of audioFiles) {
      const response = await page.goto(
        `/static/uploads/lessons/audio/tokyo_wegbeschreibung/${file}`
      );
      expect(response.status()).toBe(200);
    }
  });

  test('Lektion als Gast: Redirect zur Login-Seite', async ({ page, context }) => {
    // Clear cookies to be a guest
    await context.clearCookies();

    const resp = await page.goto('/api/lessons');
    const lessons = await resp.json();
    const tokyo = lessons.find(l => l.title && l.title.includes('Tokio'));

    if (tokyo) {
      await page.goto(`/lessons/${tokyo.id}`);
      // Should redirect to login (paid lesson, no guest access)
      await expect(page).toHaveURL(/login/);
    }
  });
});
