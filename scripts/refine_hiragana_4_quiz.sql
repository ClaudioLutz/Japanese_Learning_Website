-- Refine N5 Hiragana 4 — Quiz erweitern (lesson_content 6324)
-- 12 → 15 Fragen: Yotsugana-Regel + Wort-Bedeutung + G-Reihe-Nasalierung
SET client_encoding = 'UTF8';

BEGIN;

-- Frage 13: Wort-Bedeutung mit Diakritika (multiple_choice)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6324,
    'multiple_choice',
    'Was bedeutet 「だいがく」?',
    'Das Wort 「だいがく」 (daigaku) bedeutet **Universität**. Du erkennst だ (T+Dakuten) + い + が (K+Dakuten) + く. Beachte die G-Reihe-Nasalierung: in Wortmitte kann が wie "nga" klingen — also "dai-**nga**-ku" beim NHK-Standard.',
    'Vier Zeichen: だ + い + が + く. Hochfrequentes N5-Wort.',
    1, 1, 13, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Universität',  TRUE,  1, 'Richtig! 「だいがく」 (daigaku) = Universität.'),
  ('Schule',       FALSE, 2, '「がっこう」 (gakkou) wäre Schule.'),
  ('Buchladen',    FALSE, 3, '「ほんや」 (hon''ya) wäre Buchladen.'),
  ('Krankenhaus',  FALSE, 4, '「びょういん」 (byouin) wäre Krankenhaus.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 14: Yotsugana-Regel (true_false)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6324,
    'true_false',
    'In modernem Standard-Japanisch sollte man **immer じ und ず** schreiben — AUSSER bei Rendaku-Komposita oder Wiederholung von ち/つ, wo ぢ/づ verwendet werden.',
    'Stimmt. Das ist die Yotsugana-Standardregel von 1946: じ/ず ist die Default-Schreibung. ぢ/づ erscheint NUR in zwei Spezialfällen: (1) Rendaku — Komposita, deren zweites Morphem mit ち/つ beginnt und stimmhaft wird (z.B. はな + ち → はなぢ "Nasenbluten"); (2) Wiederholung von ち/つ im selben Wort (z.B. つづく "fortsetzen" von つ-つく). In ~98% aller Wörter ist じ/ず richtig.',
    'Erinnere dich: ぢ/づ und じ/ず klingen gleich, aber haben unterschiedliche Schreibregeln.',
    2, 1, 14, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! じ/ず ist Standard, ぢ/づ nur bei Rendaku oder Wiederholung.'),
  ('Falsch', FALSE, 2, 'Doch — das ist genau die Standard-Regel von 1946.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Frage 15: G-Reihe-Nasalierung (true_false)
WITH q AS (
  INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, hint, difficulty_level, points, order_index, created_at)
  VALUES (
    6324,
    'true_false',
    'Im NHK-Standard und bei älteren Sprechern wird die **G-Reihe in Wortmitte oft nasaliert** zu einem ng-Klang — z.B. 「かぎ」 (kagi) klingt wie "ka-**ngi**".',
    'Stimmt. Diese **Nasalierung der G-Reihe** ([ɡ] → [ŋ] in Wortmitte) ist ein Merkmal des klassischen Tokyo-Standards. Du hörst sie noch bei NHK-Nachrichten und älteren Sprechern. Bei jüngeren Sprechern und in Anime/Pop dominiert das normale [g]. Lerner müssen sie nicht aktiv produzieren, aber wiedererkennen können — relevant fürs JLPT-Hörverstehen.',
    'Denk an "ka**ng**i" für 「かぎ」 (Schlüssel) — das ist der klassische Standard.',
    2, 1, 15, NOW()
  )
  RETURNING id
)
INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback)
SELECT q.id, opt.option_text, opt.is_correct, opt.order_index, opt.feedback
FROM q,
LATERAL (VALUES
  ('Wahr',   TRUE,  1, 'Richtig! Die G-Reihe-Nasalierung ist klassischer Tokyo-Standard.'),
  ('Falsch', FALSE, 2, 'Doch — diese Nasalierung gibt es im NHK-Standard und bei älteren Sprechern.')
) AS opt(option_text, is_correct, order_index, feedback);

-- Validierung
SELECT q.id, q.question_type, LEFT(q.question_text, 60) AS preview, q.order_index, COUNT(o.id) AS options
FROM quiz_question q
LEFT JOIN quiz_option o ON o.question_id = q.id
WHERE q.lesson_content_id = 6324
GROUP BY q.id, q.question_type, q.question_text, q.order_index
ORDER BY q.order_index, q.id;

COMMIT;
