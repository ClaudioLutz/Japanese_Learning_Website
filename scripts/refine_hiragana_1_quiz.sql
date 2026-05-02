-- Refine N5 Hiragana 1 — Quiz (Lesson ID 146, lesson_content 6244)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: Wort-Bedeutung + Devoicing
-- Erwartete Zeilen pro UPDATE: 1
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung (multiple_choice) — testet Lesen + Wortverständnis
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6244,
    'multiple_choice',
    'Was bedeutet 「いし」?',
    'Das Wort 「いし」 (ishi) bedeutet **Stein**. Du erkennst い (i) + し (shi). Beachte die shi-Ausnahme!',
    'Lies das erste Zeichen, dann das zweite. Welches Wort hörst du?',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Stein', TRUE,  1, 'Richtig! 「いし」 (ishi) = Stein.'),
  ('Haus',  FALSE, 2, '「いえ」 wäre Haus — das letzte Zeichen ist hier aber 「し」 (shi).'),
  ('Salz',  FALSE, 3, '「しお」 wäre Salz — beachte die Reihenfolge der Zeichen.'),
  ('Fuss',  FALSE, 4, '「あし」 wäre Fuss — das erste Zeichen ist hier aber 「い」 (i), nicht 「あ」 (a).')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Vokal-Entstummung (true_false) — testet das neue Konzept
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6244,
    'true_false',
    'In 「です」 (desu, "ist") wird das **u** am Ende oft fast unhörbar gesprochen — es klingt wie "des".',
    'Stimmt. Das ist die **Vokal-Entstummung**: Das u zwischen oder nach stimmlosen Konsonanten (hier nach "s" am Wortende) wird hauchig oder fast stumm. Gilt auch für 「すし」 (klingt wie "s''shi") und 「ます」 (klingt wie "mas").',
    'Erinnere dich an die Regel zu "u" und "i" zwischen stimmlosen Konsonanten oder am Wortende.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! 「です」 klingt wie "des" — typische Vokal-Entstummung.'),
  ('Falsch', FALSE, 2, 'Doch — das u in "desu" wird im Standard-Tokyo-Japanisch fast immer entstummt.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung: Erwartet 14 Fragen mit ihren Optionen
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6244
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
