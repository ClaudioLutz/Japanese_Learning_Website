-- Refine N5 Katakana 5 — Quiz (Lesson ID 155, lesson_content 6498)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: Mora-Konzept + Lehnwort-Spezialitaet
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Mora-Konzept (true_false) — testet Yōon = 1 Mora
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6498,
    'true_false',
    'Eine Yōon-Silbe wie 「キャ」 (kya) zaehlt als **eine** Mora — also als ein einziger Klang im Japanischen, nicht als zwei.',
    'Stimmt. Yōon-Silben sind als EINE Mora geplant: 「キャ」 (kya) ist EIN schneller Schlag, nicht "ki-ya" mit zwei Schlaegen. Das hoert man im Sprechen klar — und es ist wichtig fuers JLPT-Hoerverstehen. 「キヤ」 (ki-ya, 2 Moren) und 「キャ」 (kya, 1 Mora) sind verschiedene Woerter!',
    'Yōon = "eine schnelle Silbe", nicht zwei separate Schlaege.',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! Yōon = 1 Mora. キャ (kya) ist EIN Klang, nicht zwei.'),
  ('Falsch', FALSE, 2, 'Doch — Yōon ist eine kompakte Silbe (1 Mora), nicht zwei separate Klaenge.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Romaji-Stolperfalle bei Yōon (multiple_choice)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6498,
    'multiple_choice',
    'Wie liest man 「シェフ」?',
    'Richtig ist **shefu** (Chef). Hier wird 「シ」 (shi) mit kleinem 「ェ」 (e) zu 「シェ」 (she) — eine Lehnwort-Spezialitaet aus dem Franzoesischen "chef". Keine separate Aussprache als "shi-e-fu" oder "she-fu" mit zwei Silben — シェ ist EINE Mora.',
    'Klein vs. gross beachten: シェ ist eine Silbe, nicht シエ (shi-e).',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('shefu',     TRUE,  1, 'Richtig! 「シェフ」 (shefu) = Chef, aus dem Franzoesischen.'),
  ('shi-e-fu',  FALSE, 2, 'Das kleine ェ ist KEIN eigener Schlag — es bildet mit シ zusammen die Silbe she.'),
  ('chefu',     FALSE, 3, '「シ」 wird "shi/she" gelesen, nicht "che". Die che-Form waere チェ.'),
  ('seefu',     FALSE, 4, 'Hier ist kein langer Vokal (kein ー nach シ). Es ist she-fu.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6498
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
