--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-0+deb12u1)
-- Dumped by pg_dump version 15.13 (Debian 15.13-0+deb12u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: course; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.course (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    background_image_url character varying(255),
    is_published boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.course OWNER TO app_user;

--
-- Name: course_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.course_id_seq OWNER TO app_user;

--
-- Name: course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.course_id_seq OWNED BY public.course.id;


--
-- Name: course_lessons; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.course_lessons (
    course_id integer NOT NULL,
    lesson_id integer NOT NULL
);


ALTER TABLE public.course_lessons OWNER TO app_user;

--
-- Name: grammar; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.grammar (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    explanation text NOT NULL,
    structure character varying(255),
    jlpt_level integer,
    example_sentences text,
    status character varying(20) DEFAULT 'approved'::character varying NOT NULL,
    created_by_ai boolean DEFAULT false NOT NULL
);


ALTER TABLE public.grammar OWNER TO app_user;

--
-- Name: grammar_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.grammar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.grammar_id_seq OWNER TO app_user;

--
-- Name: grammar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.grammar_id_seq OWNED BY public.grammar.id;


--
-- Name: kana; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.kana (
    id integer NOT NULL,
    "character" character varying(5) NOT NULL,
    romanization character varying(10) NOT NULL,
    type character varying(10) NOT NULL,
    stroke_order_info character varying(255),
    example_sound_url character varying(255)
);


ALTER TABLE public.kana OWNER TO app_user;

--
-- Name: kana_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.kana_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.kana_id_seq OWNER TO app_user;

--
-- Name: kana_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.kana_id_seq OWNED BY public.kana.id;


--
-- Name: kanji; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.kanji (
    id integer NOT NULL,
    "character" character varying(5) NOT NULL,
    meaning text NOT NULL,
    onyomi character varying(100),
    kunyomi character varying(100),
    jlpt_level integer,
    stroke_order_info character varying(255),
    radical character varying(10),
    stroke_count integer,
    status character varying(20) DEFAULT 'approved'::character varying NOT NULL,
    created_by_ai boolean DEFAULT false NOT NULL
);


ALTER TABLE public.kanji OWNER TO app_user;

--
-- Name: kanji_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.kanji_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.kanji_id_seq OWNER TO app_user;

--
-- Name: kanji_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.kanji_id_seq OWNED BY public.kanji.id;


--
-- Name: lesson; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    lesson_type character varying(20) NOT NULL,
    category_id integer,
    difficulty_level integer,
    estimated_duration integer,
    order_index integer DEFAULT 0,
    is_published boolean DEFAULT false,
    allow_guest_access boolean DEFAULT false NOT NULL,
    instruction_language character varying(10) DEFAULT 'english'::character varying NOT NULL,
    thumbnail_url character varying(255),
    background_image_url character varying(1000),
    background_image_path character varying(500),
    video_intro_url character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    price real DEFAULT 0.0 NOT NULL,
    is_purchasable boolean DEFAULT false NOT NULL
);


ALTER TABLE public.lesson OWNER TO app_user;

--
-- Name: lesson_category; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson_category (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    color_code character varying(7) DEFAULT '#007bff'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.lesson_category OWNER TO app_user;

--
-- Name: lesson_category_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_category_id_seq OWNER TO app_user;

--
-- Name: lesson_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_category_id_seq OWNED BY public.lesson_category.id;


--
-- Name: lesson_content; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson_content (
    id integer NOT NULL,
    lesson_id integer NOT NULL,
    content_type character varying(20) NOT NULL,
    content_id integer,
    title character varying(200),
    content_text text,
    media_url character varying(255),
    order_index integer DEFAULT 0,
    page_number integer DEFAULT 1 NOT NULL,
    is_optional boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    file_path character varying(500),
    file_size integer,
    file_type character varying(50),
    original_filename character varying(255),
    is_interactive boolean DEFAULT false,
    quiz_type character varying(50) DEFAULT 'standard'::character varying,
    max_attempts integer DEFAULT 3,
    passing_score integer DEFAULT 70,
    generated_by_ai boolean DEFAULT false NOT NULL,
    ai_generation_details jsonb
);


ALTER TABLE public.lesson_content OWNER TO app_user;

--
-- Name: lesson_content_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_content_id_seq OWNER TO app_user;

--
-- Name: lesson_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_content_id_seq OWNED BY public.lesson_content.id;


--
-- Name: lesson_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_id_seq OWNER TO app_user;

--
-- Name: lesson_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_id_seq OWNED BY public.lesson.id;


--
-- Name: lesson_page; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson_page (
    id integer NOT NULL,
    lesson_id integer NOT NULL,
    page_number integer NOT NULL,
    title character varying(200),
    description text
);


ALTER TABLE public.lesson_page OWNER TO app_user;

--
-- Name: lesson_page_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_page_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_page_id_seq OWNER TO app_user;

--
-- Name: lesson_page_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_page_id_seq OWNED BY public.lesson_page.id;


--
-- Name: lesson_prerequisite; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson_prerequisite (
    id integer NOT NULL,
    lesson_id integer NOT NULL,
    prerequisite_lesson_id integer NOT NULL
);


ALTER TABLE public.lesson_prerequisite OWNER TO app_user;

--
-- Name: lesson_prerequisite_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_prerequisite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_prerequisite_id_seq OWNER TO app_user;

--
-- Name: lesson_prerequisite_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_prerequisite_id_seq OWNED BY public.lesson_prerequisite.id;


--
-- Name: lesson_purchase; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.lesson_purchase (
    id integer NOT NULL,
    user_id integer NOT NULL,
    lesson_id integer NOT NULL,
    price_paid real NOT NULL,
    purchased_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    stripe_payment_intent_id character varying(100)
);


ALTER TABLE public.lesson_purchase OWNER TO app_user;

--
-- Name: lesson_purchase_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.lesson_purchase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lesson_purchase_id_seq OWNER TO app_user;

--
-- Name: lesson_purchase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.lesson_purchase_id_seq OWNED BY public.lesson_purchase.id;


--
-- Name: quiz_option; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.quiz_option (
    id integer NOT NULL,
    question_id integer NOT NULL,
    option_text text NOT NULL,
    is_correct boolean DEFAULT false,
    order_index integer DEFAULT 0,
    feedback text
);


ALTER TABLE public.quiz_option OWNER TO app_user;

--
-- Name: quiz_option_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.quiz_option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.quiz_option_id_seq OWNER TO app_user;

--
-- Name: quiz_option_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.quiz_option_id_seq OWNED BY public.quiz_option.id;


--
-- Name: quiz_question; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.quiz_question (
    id integer NOT NULL,
    lesson_content_id integer NOT NULL,
    question_type character varying(50) NOT NULL,
    question_text text NOT NULL,
    explanation text,
    hint text,
    difficulty_level integer DEFAULT 1,
    points integer DEFAULT 1,
    order_index integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.quiz_question OWNER TO app_user;

--
-- Name: quiz_question_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.quiz_question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.quiz_question_id_seq OWNER TO app_user;

--
-- Name: quiz_question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.quiz_question_id_seq OWNED BY public.quiz_question.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256) NOT NULL,
    subscription_level character varying(50) DEFAULT 'free'::character varying,
    is_admin boolean DEFAULT false NOT NULL
);


ALTER TABLE public."user" OWNER TO app_user;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO app_user;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: user_lesson_progress; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.user_lesson_progress (
    id integer NOT NULL,
    user_id integer NOT NULL,
    lesson_id integer NOT NULL,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    is_completed boolean DEFAULT false,
    progress_percentage integer DEFAULT 0,
    time_spent integer DEFAULT 0,
    last_accessed timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    content_progress text
);


ALTER TABLE public.user_lesson_progress OWNER TO app_user;

--
-- Name: user_lesson_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.user_lesson_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_lesson_progress_id_seq OWNER TO app_user;

--
-- Name: user_lesson_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.user_lesson_progress_id_seq OWNED BY public.user_lesson_progress.id;


--
-- Name: user_quiz_answer; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.user_quiz_answer (
    id integer NOT NULL,
    user_id integer NOT NULL,
    question_id integer NOT NULL,
    selected_option_id integer,
    text_answer text,
    is_correct boolean DEFAULT false,
    answered_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    attempts integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.user_quiz_answer OWNER TO app_user;

--
-- Name: user_quiz_answer_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.user_quiz_answer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_quiz_answer_id_seq OWNER TO app_user;

--
-- Name: user_quiz_answer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.user_quiz_answer_id_seq OWNED BY public.user_quiz_answer.id;


--
-- Name: vocabulary; Type: TABLE; Schema: public; Owner: app_user
--

CREATE TABLE public.vocabulary (
    id integer NOT NULL,
    word character varying(100) NOT NULL,
    reading character varying(100) NOT NULL,
    meaning text NOT NULL,
    jlpt_level integer,
    example_sentence_japanese text,
    example_sentence_english text,
    audio_url character varying(255),
    status character varying(20) DEFAULT 'approved'::character varying NOT NULL,
    created_by_ai boolean DEFAULT false NOT NULL
);


ALTER TABLE public.vocabulary OWNER TO app_user;

--
-- Name: vocabulary_id_seq; Type: SEQUENCE; Schema: public; Owner: app_user
--

CREATE SEQUENCE public.vocabulary_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vocabulary_id_seq OWNER TO app_user;

--
-- Name: vocabulary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: app_user
--

ALTER SEQUENCE public.vocabulary_id_seq OWNED BY public.vocabulary.id;


--
-- Name: course id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.course ALTER COLUMN id SET DEFAULT nextval('public.course_id_seq'::regclass);


--
-- Name: grammar id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.grammar ALTER COLUMN id SET DEFAULT nextval('public.grammar_id_seq'::regclass);


--
-- Name: kana id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kana ALTER COLUMN id SET DEFAULT nextval('public.kana_id_seq'::regclass);


--
-- Name: kanji id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kanji ALTER COLUMN id SET DEFAULT nextval('public.kanji_id_seq'::regclass);


--
-- Name: lesson id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson ALTER COLUMN id SET DEFAULT nextval('public.lesson_id_seq'::regclass);


--
-- Name: lesson_category id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_category ALTER COLUMN id SET DEFAULT nextval('public.lesson_category_id_seq'::regclass);


--
-- Name: lesson_content id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_content ALTER COLUMN id SET DEFAULT nextval('public.lesson_content_id_seq'::regclass);


--
-- Name: lesson_page id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_page ALTER COLUMN id SET DEFAULT nextval('public.lesson_page_id_seq'::regclass);


--
-- Name: lesson_prerequisite id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_prerequisite ALTER COLUMN id SET DEFAULT nextval('public.lesson_prerequisite_id_seq'::regclass);


--
-- Name: lesson_purchase id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_purchase ALTER COLUMN id SET DEFAULT nextval('public.lesson_purchase_id_seq'::regclass);


--
-- Name: quiz_option id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_option ALTER COLUMN id SET DEFAULT nextval('public.quiz_option_id_seq'::regclass);


--
-- Name: quiz_question id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_question ALTER COLUMN id SET DEFAULT nextval('public.quiz_question_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: user_lesson_progress id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_lesson_progress ALTER COLUMN id SET DEFAULT nextval('public.user_lesson_progress_id_seq'::regclass);


--
-- Name: user_quiz_answer id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer ALTER COLUMN id SET DEFAULT nextval('public.user_quiz_answer_id_seq'::regclass);


--
-- Name: vocabulary id; Type: DEFAULT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.vocabulary ALTER COLUMN id SET DEFAULT nextval('public.vocabulary_id_seq'::regclass);


--
-- Name: course_lessons course_lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.course_lessons
    ADD CONSTRAINT course_lessons_pkey PRIMARY KEY (course_id, lesson_id);


--
-- Name: course course_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_pkey PRIMARY KEY (id);


--
-- Name: grammar grammar_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.grammar
    ADD CONSTRAINT grammar_pkey PRIMARY KEY (id);


--
-- Name: grammar grammar_title_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.grammar
    ADD CONSTRAINT grammar_title_key UNIQUE (title);


--
-- Name: kana kana_character_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kana
    ADD CONSTRAINT kana_character_key UNIQUE ("character");


--
-- Name: kana kana_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kana
    ADD CONSTRAINT kana_pkey PRIMARY KEY (id);


--
-- Name: kanji kanji_character_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kanji
    ADD CONSTRAINT kanji_character_key UNIQUE ("character");


--
-- Name: kanji kanji_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.kanji
    ADD CONSTRAINT kanji_pkey PRIMARY KEY (id);


--
-- Name: lesson_category lesson_category_name_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_category
    ADD CONSTRAINT lesson_category_name_key UNIQUE (name);


--
-- Name: lesson_category lesson_category_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_category
    ADD CONSTRAINT lesson_category_pkey PRIMARY KEY (id);


--
-- Name: lesson_content lesson_content_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_content
    ADD CONSTRAINT lesson_content_pkey PRIMARY KEY (id);


--
-- Name: lesson_page lesson_page_lesson_id_page_number_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_page
    ADD CONSTRAINT lesson_page_lesson_id_page_number_key UNIQUE (lesson_id, page_number);


--
-- Name: lesson_page lesson_page_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_page
    ADD CONSTRAINT lesson_page_pkey PRIMARY KEY (id);


--
-- Name: lesson lesson_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson
    ADD CONSTRAINT lesson_pkey PRIMARY KEY (id);


--
-- Name: lesson_prerequisite lesson_prerequisite_lesson_id_prerequisite_lesson_id_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_prerequisite
    ADD CONSTRAINT lesson_prerequisite_lesson_id_prerequisite_lesson_id_key UNIQUE (lesson_id, prerequisite_lesson_id);


--
-- Name: lesson_prerequisite lesson_prerequisite_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_prerequisite
    ADD CONSTRAINT lesson_prerequisite_pkey PRIMARY KEY (id);


--
-- Name: lesson_purchase lesson_purchase_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_purchase
    ADD CONSTRAINT lesson_purchase_pkey PRIMARY KEY (id);


--
-- Name: lesson_purchase lesson_purchase_user_id_lesson_id_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_purchase
    ADD CONSTRAINT lesson_purchase_user_id_lesson_id_key UNIQUE (user_id, lesson_id);


--
-- Name: quiz_option quiz_option_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_option
    ADD CONSTRAINT quiz_option_pkey PRIMARY KEY (id);


--
-- Name: quiz_question quiz_question_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_question
    ADD CONSTRAINT quiz_question_pkey PRIMARY KEY (id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user_lesson_progress user_lesson_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_lesson_progress
    ADD CONSTRAINT user_lesson_progress_pkey PRIMARY KEY (id);


--
-- Name: user_lesson_progress user_lesson_progress_user_id_lesson_id_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_lesson_progress
    ADD CONSTRAINT user_lesson_progress_user_id_lesson_id_key UNIQUE (user_id, lesson_id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_quiz_answer user_quiz_answer_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer
    ADD CONSTRAINT user_quiz_answer_pkey PRIMARY KEY (id);


--
-- Name: user_quiz_answer user_quiz_answer_user_id_question_id_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer
    ADD CONSTRAINT user_quiz_answer_user_id_question_id_key UNIQUE (user_id, question_id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: vocabulary vocabulary_pkey; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.vocabulary
    ADD CONSTRAINT vocabulary_pkey PRIMARY KEY (id);


--
-- Name: vocabulary vocabulary_word_key; Type: CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.vocabulary
    ADD CONSTRAINT vocabulary_word_key UNIQUE (word);


--
-- Name: idx_lesson_category; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_category ON public.lesson USING btree (category_id);


--
-- Name: idx_lesson_content_lesson; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_content_lesson ON public.lesson_content USING btree (lesson_id);


--
-- Name: idx_lesson_content_page; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_content_page ON public.lesson_content USING btree (page_number);


--
-- Name: idx_lesson_prerequisite_lesson; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_prerequisite_lesson ON public.lesson_prerequisite USING btree (lesson_id);


--
-- Name: idx_lesson_prerequisite_prereq; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_prerequisite_prereq ON public.lesson_prerequisite USING btree (prerequisite_lesson_id);


--
-- Name: idx_lesson_purchase_user; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_lesson_purchase_user ON public.lesson_purchase USING btree (user_id);


--
-- Name: idx_quiz_option_question; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_quiz_option_question ON public.quiz_option USING btree (question_id);


--
-- Name: idx_quiz_question_content; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_quiz_question_content ON public.quiz_question USING btree (lesson_content_id);


--
-- Name: idx_user_progress_lesson; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_user_progress_lesson ON public.user_lesson_progress USING btree (lesson_id);


--
-- Name: idx_user_progress_user; Type: INDEX; Schema: public; Owner: app_user
--

CREATE INDEX idx_user_progress_user ON public.user_lesson_progress USING btree (user_id);


--
-- Name: course_lessons course_lessons_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.course_lessons
    ADD CONSTRAINT course_lessons_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(id);


--
-- Name: course_lessons course_lessons_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.course_lessons
    ADD CONSTRAINT course_lessons_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson lesson_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson
    ADD CONSTRAINT lesson_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.lesson_category(id);


--
-- Name: lesson_content lesson_content_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_content
    ADD CONSTRAINT lesson_content_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson_page lesson_page_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_page
    ADD CONSTRAINT lesson_page_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson_prerequisite lesson_prerequisite_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_prerequisite
    ADD CONSTRAINT lesson_prerequisite_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson_prerequisite lesson_prerequisite_prerequisite_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_prerequisite
    ADD CONSTRAINT lesson_prerequisite_prerequisite_lesson_id_fkey FOREIGN KEY (prerequisite_lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson_purchase lesson_purchase_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_purchase
    ADD CONSTRAINT lesson_purchase_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: lesson_purchase lesson_purchase_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.lesson_purchase
    ADD CONSTRAINT lesson_purchase_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: quiz_option quiz_option_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_option
    ADD CONSTRAINT quiz_option_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.quiz_question(id);


--
-- Name: quiz_question quiz_question_lesson_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.quiz_question
    ADD CONSTRAINT quiz_question_lesson_content_id_fkey FOREIGN KEY (lesson_content_id) REFERENCES public.lesson_content(id);


--
-- Name: user_lesson_progress user_lesson_progress_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_lesson_progress
    ADD CONSTRAINT user_lesson_progress_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(id);


--
-- Name: user_lesson_progress user_lesson_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_lesson_progress
    ADD CONSTRAINT user_lesson_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_quiz_answer user_quiz_answer_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer
    ADD CONSTRAINT user_quiz_answer_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.quiz_question(id);


--
-- Name: user_quiz_answer user_quiz_answer_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer
    ADD CONSTRAINT user_quiz_answer_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.quiz_option(id);


--
-- Name: user_quiz_answer user_quiz_answer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: app_user
--

ALTER TABLE ONLY public.user_quiz_answer
    ADD CONSTRAINT user_quiz_answer_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO app_user;


--
-- PostgreSQL database dump complete
--

