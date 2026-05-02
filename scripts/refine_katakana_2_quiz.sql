-- Refine N5 Katakana 2 — Quiz (Lesson ID 152, lesson_content 6409)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: Aussprache-Ausnahme + Devoicing-Wort
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung (multiple_choice) — testet Lesen + Wortverstaendnis
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6409,
    'multiple_choice',
    'Was bedeutet 「テスト」?',
    'Das Wort 「テスト」 (tesuto) bedeutet **Test/Pruefung** — Lehnwort aus dem Englischen "test". Du erkennst テ + ス + ト. Im Sprechen wird das u zwischen s und t entstummt: klingt fast wie "tes''to".',
    'Lies Zeichen fuer Zeichen: テ + ス + ト. Welches englische Wort steckt dahinter?',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Test/Pruefung', TRUE,  1, 'Richtig! 「テスト」 (tesuto) = Test, aus dem Englischen.'),
  ('Tisch',         FALSE, 2, 'Tisch waere 「テーブル」 (tēburu) — viel laenger.'),
  ('Toast',         FALSE, 3, 'Toast waere 「トースト」 (tōsuto) — beachte den Laengungsstrich nach ト.'),
  ('Trick',         FALSE, 4, 'Trick waere 「トリック」 (torikku) — andere Zeichen.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Aussprache-Ausnahme チ (true_false) — testet Konzept
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6409,
    'true_false',
    'Das Zeichen 「チ」 wird wie das deutsche **"ti"** (in *Tisch*) ausgesprochen.',
    'Falsch. 「チ」 wird **"chi"** ausgesprochen — wie das "tschi" in *Tschuess*. Das ist eine der drei Aussprache-Ausnahmen der T-Reihe (zusammen mit ツ = tsu und der Reihen-Ausnahme フ = fu in der H-Reihe).',
    'Erinnere dich: T-Reihe hat ZWEI Ausnahmen mitten in der Reihe.',
    1, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   FALSE, 1, 'Falsch. 「チ」 wird **chi** (tschi) ausgesprochen, nicht ti.'),
  ('Falsch', TRUE,  2, 'Richtig! 「チ」 = chi (tschi), nicht ti. Eine der drei Ausnahmen der Lektion.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6409
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
