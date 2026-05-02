-- Refine N5 Hiragana 3 — Quiz erweitern (lesson_content 6290)
-- 12 → 14 Fragen: Wort-Bedeutung + ん-Assimilation
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung (multiple_choice) — testet Lesen + R-Reihe
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6290,
    'multiple_choice',
    'Was bedeutet 「さくら」?',
    'Das Wort 「さくら」 (sakura) bedeutet **Kirschblüte** — das Symbol des japanischen Frühlings. Beachte: Das **r** in さくら ist ein Tap [ɾ] (Zungenspitze tippt einmal kurz an den Gaumen), kein gerolltes deutsches R.',
    'Drei Zeichen: さ (sa) + く (ku) + ら (ra). Sehr berühmtes japanisches Wort.',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Kirschblüte',  TRUE,  1, 'Richtig! 「さくら」 (sakura) = Kirschblüte. R wird als Tap gesprochen.'),
  ('Sushi',        FALSE, 2, '「すし」 wäre Sushi — andere Zeichen.'),
  ('Sonne',        FALSE, 3, '「ひ」 oder 「たいよう」 wäre Sonne.'),
  ('Berg',         FALSE, 4, '「やま」 wäre Berg — kommt mit der Y-Reihe vor.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: ん-Assimilation (true_false)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6290,
    'true_false',
    'In 「りんご」 (ringo, "Apfel") klingt das **ん** wie das **ng** in "Singen" — nicht wie ein normales "n".',
    'Stimmt. Das ist die ん-Assimilation: **vor k oder g** wird 「ん」 zu einem **velaren Nasal [ŋ]** — klingt wie das deutsche **ng** in *Singer*. Weiteres Beispiel: 「ぎんこう」 (ginkou, "Bank") wird "gin-kou" mit ng-Laut zwischen gin und kou. Andere Varianten: vor m/p/b → "m" (sampo), vor n/t/d → "n" (mikan, am Wortende).',
    'Erinnere dich: 「ん」 hat vier Klang-Varianten je nach Folge-Konsonant.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! Vor k/g wird ん zu ng. 「りんご」 = "ringo" mit ng-Klang.'),
  ('Falsch', FALSE, 2, 'Doch — vor k oder g wird ん immer zu einem velaren Nasal (ng-Klang).')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6290
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
