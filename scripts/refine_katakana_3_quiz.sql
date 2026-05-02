-- Refine N5 Katakana 3 — Quiz (Lesson ID 153, lesson_content 6433)
-- Erweitert das bestehende 12er-Quiz um 2 Fragen: ヲ-Sonderrolle + ン-Aussprache
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: ヲ-Sonderrolle (multiple_choice) — testet Konzept aus Lektion
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6433,
    'multiple_choice',
    'Wie wird das Zeichen 「ヲ」 ausgesprochen?',
    'Richtig ist **"o"**. Obwohl ヲ in der Tabelle als "wo" gefuehrt wird, spricht man es im modernen Japanisch wie ein einfaches **o**. In Katakana siehst du ヲ extrem selten — fast nur in alten Texten oder Liedtiteln. Im Hiragana ist 「を」 dagegen die wichtige Akkusativ-Partikel.',
    'Auch in Hiragana wird das entsprechende 「を」 wie "o" gesprochen, nicht wie "wo".',
    2, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('o',  TRUE,  1, 'Richtig! ヲ wird wie "o" gesprochen — historisches Erbe.'),
  ('wo', FALSE, 2, 'Im modernen Japanisch wird das w nicht mehr gesprochen — nur "o".'),
  ('vo', FALSE, 3, 'ヲ hat keinen v-Klang. Fuer "vo" verwendet man ヴォ (Lehnwort-Schreibung).'),
  ('uo', FALSE, 4, 'ヲ ist ein einzelner Klang "o", nicht eine Silbenkombination.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: ン-Aussprache (true_false) — testet Konzept der 6 Varianten
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6433,
    'true_false',
    'In 「コンビニ」 (konbini, "Convenience-Store") klingt das ン vor dem b wie ein **m** — also fast "kombini".',
    'Stimmt. ン ist ein "Aussprache-Chamaeleon": vor m, p, b wird es als **m** realisiert; vor k, g als **ng**; vor t, d, n, r, s, ts, z als **n**; am Wortende als nasaliertes N. Du musst das nicht aktiv lernen — dein Mund passt sich automatisch an, sobald du den naechsten Konsonanten ansetzt.',
    'Erinnere dich: ン hat sechs Aussprache-Varianten je nach Folgekonsonant.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! ン vor b/p/m wird zu m — daher "kombini" statt "konbini".'),
  ('Falsch', FALSE, 2, 'Doch — vor m, p, b wird ン automatisch als m realisiert. Das ist eine der sechs Varianten.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6433
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
