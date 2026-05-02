-- Refine N5 Hiragana 5 — Quiz erweitern (lesson_content 6365)
-- 12 → 14 Fragen: Mora-Konzept + Wort-Bedeutung
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung mit Yoon (multiple_choice)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6365,
    'multiple_choice',
    'Was bedeutet 「ぎゅうにゅう」?',
    'Das Wort 「ぎゅうにゅう」 (gyuunyuu) bedeutet **Milch**. Du erkennst ぎゅ (gyu, Yōon!) + う + に + ゅ (Yōon nyu) + う. Insgesamt sind das **4 Mora** (gyu-u-nyu-u), nicht 6 — die kleinen ゅ verschmelzen mit dem vorhergehenden Zeichen.',
    'Fünf Schriftzeichen, zwei davon Yōon: ぎゅう + にゅう. Hochfrequentes Alltagswort.',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Milch',         TRUE,  1, 'Richtig! 「ぎゅうにゅう」 (gyuunyuu) = Milch. 4 Mora.'),
  ('Wasser',        FALSE, 2, '「みず」 wäre Wasser — keine Yōon nötig.'),
  ('Tee',           FALSE, 3, '「おちゃ」 wäre Tee — auch ein Yōon, aber anderes Wort.'),
  ('Reis/Mahlzeit', FALSE, 4, '「ごはん」 wäre Reis/Mahlzeit.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Mora-Zaehlung (true_false)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6365,
    'true_false',
    'Das Wort 「びょういん」 (byouin, "Krankenhaus") besteht aus **4 Mora** — und ist damit ein Mora kürzer als 「びよういん」 (biyouin, "Schönheitssalon", 5 Mora).',
    'Stimmt. **Mora-Aufschlüsselung:** 「びょういん」 = bjo (Yōon, 1 Mora) + u (1) + i (1) + n (1, Moraic Nasal) = **4 Mora**. 「びよういん」 = bi (1) + yo (1) + u (1) + i (1) + n (1) = **5 Mora**. Yōon spart genau eine Mora — und das macht oft den Bedeutungsunterschied. Der gleiche Mechanismus gilt für じゅう (juu, "10", 2 Mora) vs じゆう (jiyuu, "Freiheit", 3 Mora).',
    'Yōon = 1 Mora, gross ya/yu/yo = 2 Mora. Das macht den Mora-Unterschied zwischen den beiden Wörtern.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! Yōon spart eine Mora — びょういん ist kürzer als びよういん.'),
  ('Falsch', FALSE, 2, 'Doch — Yōon ist 1 Mora, gross ya/yu/yo ist 2 Mora.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6365
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
