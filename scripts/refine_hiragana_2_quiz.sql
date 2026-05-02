-- Refine N5 Hiragana 2 — Quiz erweitern (lesson_content 6266)
-- 12 → 14 Fragen: Wort-Bedeutung + は-als-Partikel
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung mit Devoicing-Hinweis (multiple_choice)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6266,
    'multiple_choice',
    'Was bedeutet 「ひと」 (gesprochen "h''to")?',
    'Das Wort 「ひと」 (hito) bedeutet **Mensch** oder **Person**. Das **i** zwischen "h" und "t" wird **entstummt** — es klingt wie "h''to". Diese Vokal-Entstummung ist Standard im Tokyo-Japanisch.',
    'Zwei Zeichen: ひ (hi) + と (to). Ein sehr hochfrequentes Wort.',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Mensch / Person', TRUE,  1, 'Richtig! 「ひと」 (hito) = Mensch. Das i wird entstummt → "h''to".'),
  ('Sonne',           FALSE, 2, '「ひ」 allein kann "Sonne/Tag" heissen, aber 「ひと」 ist ein anderes Wort.'),
  ('Boot',            FALSE, 3, '「ふね」 (fune) wäre Boot — andere Zeichen.'),
  ('Hand',            FALSE, 4, '「て」 (te) wäre Hand — nur ein Zeichen.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: は-als-Partikel-Regel (true_false)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6266,
    'true_false',
    'Wenn 「は」 als Themen-Partikel im Satz steht (z.B. 「わたしは…」), wird es **"wa"** ausgesprochen — auch wenn das Zeichen 「は」 bleibt.',
    'Stimmt. Das ist die berühmte は-Sonderregel: Als Bestandteil von Wörtern (はな, はし) bleibt 「は」 = "ha". Als Partikel nach einem Wort wird 「は」 = "wa". Geschrieben wird es immer 「は」 — die Aussprache hängt von der Funktion ab. Historischer Hintergrund: Reste der älteren Kana-Schreibung.',
    'Erinnere dich: Es gibt zwei Lese-Fälle für 「は」 — einer in normalen Wörtern, einer als Partikel.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! 「は」 als Partikel = "wa". 「わたしは」 → "watashi wa".'),
  ('Falsch', FALSE, 2, 'Doch — das ist genau die Sonderregel. 「は」 als Themen-Partikel wird "wa" gesprochen.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6266
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
