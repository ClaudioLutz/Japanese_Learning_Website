-- Refine N5 Katakana 1 — Quiz (Lesson ID 151, lesson_content 6387)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: Längungsstrich + Devoicing
-- Erwartete Zeilen pro INSERT: 1 Question + 4 Optionen (bzw. 2 fuer true_false)
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Laengungsstrich (multiple_choice) — Katakana-spezifisches Konzept
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6387,
    'multiple_choice',
    'Wie liest man 「コーヒー」?',
    'Richtig ist **kōhī**. Der Laengungsstrich 「ー」 verlaengert den vorherigen Vokal: コ + ー = kō, ヒ + ー = hī. So entsteht aus dem englischen *coffee* das japanische ko-h-i mit zwei langen Vokalen.',
    'Der Strich 「ー」 verlaengert den Vokal davor — er ist KEIN eigenes Zeichen.',
    2, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('kōhī (langes o, langes i)', TRUE,  1, 'Richtig! 「コーヒー」 (kōhī) = Kaffee. Der Laengungsstrich verlaengert beide Vokale.'),
  ('kohi (kurze Vokale)',        FALSE, 2, 'Der Laengungsstrich 「ー」 wird nicht ignoriert — er VERLAENGERT den vorherigen Vokal.'),
  ('koohi (zwei o)',             FALSE, 3, 'In Katakana wird Vokalverlaengerung NICHT durch Wiederholung geschrieben (das ist Hiragana). Hier nutzt man 「ー」.'),
  ('konhī',                      FALSE, 4, 'Der Strich 「ー」 ist kein "n" und auch keine eigene Silbe — er ist ein reines Verlaengerungszeichen.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Vokal-Entstummung (true_false) — gleiches Konzept wie H1, jetzt mit Katakana-Wort
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6387,
    'true_false',
    'In 「スキ」 (suki, "Ski") wird das **u** zwischen s und k oft fast unhoerbar gesprochen — es klingt wie "ski".',
    'Stimmt. Das ist die **Vokal-Entstummung**: Das u zwischen zwei stimmlosen Konsonanten (s und k) wird hauchig oder fast stumm. Das gilt auch fuer Hiragana — Katakana hat dieselbe Phonologie. Beispiele: 「キス」 (kisu) klingt wie "kis", 「クス」 wie "k''su".',
    'Erinnere dich an die Regel zu "u" und "i" zwischen stimmlosen Konsonanten.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! 「スキ」 klingt wie "ski" — typische Vokal-Entstummung im Tokyo-Standard.'),
  ('Falsch', FALSE, 2, 'Doch — das u zwischen den stimmlosen Konsonanten s und k wird im Standard-Japanisch fast immer entstummt.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung: Erwartet 14 Fragen mit ihren Optionen
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6387
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
