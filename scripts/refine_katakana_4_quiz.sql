-- Refine N5 Katakana 4 — Quiz (Lesson ID 154, lesson_content 6467)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: Yotsugana + Dakuten-Mechanik
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Yotsugana (multiple_choice) — testet Konzept
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6467,
    'multiple_choice',
    'Du moechtest "ji" in einem Katakana-Lehnwort schreiben (z.B. "Jeans"). Welches Zeichen verwendest du?',
    'Richtig ist **ジ**. Im modernen Japanisch (seit der Rechtschreibreform 1946) wird *ji* fast immer als 「ジ」 geschrieben. Das Zeichen 「ヂ」 klingt identisch, ist aber ein **Yotsugana-Relikt** (vier Kana, die historisch verschiedene Klaenge hatten). In Katakana-Lehnwoertern siehst du ヂ extrem selten — Faustregel: bei Unsicherheit immer ジ und ズ verwenden.',
    'Welches der zwei ji-Zeichen ist Standard? ジ (aus S-Reihe) oder ヂ (aus T-Reihe)?',
    2, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('ジ',        TRUE,  1, 'Richtig! ジ ist die Standard-Form fuer ji im modernen Japanisch.'),
  ('ヂ',        FALSE, 2, 'ヂ klingt zwar identisch, ist aber ein Yotsugana-Relikt — fast nie verwendet.'),
  ('ジー',      FALSE, 3, 'Das ist "jī" mit Laengungsstrich — laenger, nicht das Standard-ji.'),
  ('シ',        FALSE, 4, 'シ ohne Dakuten waere "shi" (stimmlos), nicht "ji".')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Dakuten-Mechanik (true_false) — testet, was Dakuten genau bewirkt
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6467,
    'true_false',
    'Dakuten 「゛」 macht **stimmlose** Konsonanten **stimmhaft** (k → g, s → z, t → d, h → b). Handakuten 「゜」 wirkt dagegen NUR auf die H-Reihe (h → p).',
    'Stimmt. Dakuten ist die universelle Stimmhaftigkeitsmarkierung — sie modifiziert vier Reihen (K/S/T/H). Handakuten ist die Spezial-Markierung fuer die P-Reihe und wirkt NUR auf H. Spannend: Handakuten wurde im 16. Jh. von portugiesischen Jesuiten erfunden, weil sie ein eindeutiges Zeichen fuer /p/ und /f/ brauchten — daher ist die P-Reihe in Katakana-Lehnwoertern so haeufig.',
    'Pruefe: Dakuten = wie viele Reihen? Handakuten = wie viele Reihen?',
    1, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! Dakuten = vier Reihen (K/S/T/H), Handakuten = nur H-Reihe.'),
  ('Falsch', FALSE, 2, 'Doch — die Aussage stimmt. Dakuten wirkt auf K/S/T/H, Handakuten nur auf H.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6467
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
