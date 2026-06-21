-- Dump: ein voll aufgeloestes JSON pro published Lektion (fuer didaktischen Audit)
-- Aufruf: ssh hp-ubuntu "sudo docker exec -i postgres_db psql -U app_user -d japanese_learning -t -A -f -" < diese_datei
SELECT json_build_object(
  'id', l.id,
  'title', l.title,
  'description', l.description,
  'lesson_type', l.lesson_type,
  'difficulty_level', l.difficulty_level,
  'instruction_language', l.instruction_language,
  'order_index', l.order_index,
  'category', cat.name,
  'category_jlpt_level', cat.jlpt_level,
  'category_order', cat.display_order,
  'pages', (
    SELECT json_agg(page_obj ORDER BY pn)
    FROM (
      SELECT ps.pn AS pn,
        json_build_object(
          'page_number', ps.pn,
          'title', (SELECT lp.title FROM lesson_page lp WHERE lp.lesson_id = l.id AND lp.page_number = ps.pn),
          'page_type', (SELECT lp.page_type FROM lesson_page lp WHERE lp.lesson_id = l.id AND lp.page_number = ps.pn),
          'content', (
            SELECT json_agg(c_obj ORDER BY ord)
            FROM (
              SELECT lc.order_index AS ord,
                json_build_object(
                  'order_index', lc.order_index,
                  'content_type', lc.content_type,
                  'title', lc.title,
                  'content_text', lc.content_text,
                  'is_interactive', lc.is_interactive,
                  'is_optional', lc.is_optional,
                  'resolved', CASE lc.content_type
                    WHEN 'vocabulary' THEN (SELECT row_to_json(x) FROM (SELECT v.word, v.reading, v.romaji, v.meaning, v.meaning_de, v.jlpt_level, v.example_sentence_japanese, v.example_sentence_english FROM vocabulary v WHERE v.id = lc.content_id) x)
                    WHEN 'kanji' THEN (SELECT row_to_json(x) FROM (SELECT k.character, k.meaning, k.onyomi, k.kunyomi, k.jlpt_level FROM kanji k WHERE k.id = lc.content_id) x)
                    WHEN 'kana' THEN (SELECT row_to_json(x) FROM (SELECT ka.character, ka.romanization, ka.type, ka.mnemonic FROM kana ka WHERE ka.id = lc.content_id) x)
                    WHEN 'grammar' THEN (SELECT row_to_json(x) FROM (SELECT g.title, g.explanation, g.structure, g.jlpt_level, g.example_sentences, g.nuance, g.romaji FROM grammar g WHERE g.id = lc.content_id) x)
                    ELSE NULL END,
                  'quiz', (
                    SELECT json_agg(q_obj ORDER BY qord)
                    FROM (
                      SELECT qq.order_index AS qord,
                        json_build_object(
                          'question_type', qq.question_type,
                          'question_text', qq.question_text,
                          'explanation', qq.explanation,
                          'hint', qq.hint,
                          'options', (SELECT json_agg(json_build_object('option_text', qo.option_text, 'is_correct', qo.is_correct, 'feedback', qo.feedback) ORDER BY qo.order_index) FROM quiz_option qo WHERE qo.question_id = qq.id)
                        ) AS q_obj
                      FROM quiz_question qq WHERE qq.lesson_content_id = lc.id
                    ) qsub
                  )
                ) AS c_obj
              FROM lesson_content lc
              WHERE lc.lesson_id = l.id AND lc.page_number = ps.pn
            ) csub
          )
        ) AS page_obj
      FROM (SELECT DISTINCT page_number AS pn FROM lesson_content WHERE lesson_id = l.id) ps
    ) psub
  )
)
FROM lesson l
LEFT JOIN lesson_category cat ON cat.id = l.category_id
WHERE l.is_published = true
ORDER BY l.id;
