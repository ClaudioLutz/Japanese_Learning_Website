# Database Schema

## 1. Introduction

The Japanese Learning Website utilizes a relational database managed by SQLAlchemy ORM. The schema is designed to support user management, content organization (Kana, Kanji, Vocabulary, Grammar), a comprehensive lesson system with progress tracking, and interactive quiz functionalities. Database migrations are handled by Alembic.

This document outlines the structure of each table (model) in the database.

## 2. Core Models

### 2.1. `User`

Stores information about registered users, including authentication details, subscription level, and admin status.

| Column             | Type          | Constraints                                  | Description                                                                 |
|--------------------|---------------|----------------------------------------------|-----------------------------------------------------------------------------|
| `id`               | Integer       | Primary Key                                  | Unique identifier for the user.                                             |
| `username`         | String(80)    | Unique, Not Nullable                         | User's chosen username.                                                     |
| `email`            | String(120)   | Unique, Not Nullable                         | User's email address, used for login.                                       |
| `password_hash`    | String(256)   | Not Nullable                                 | Hashed password for secure authentication.                                  |
| `subscription_level`| String(50)    | Default: 'free'                              | User's subscription tier (e.g., 'free', 'premium').                           |
| `is_admin`         | Boolean       | Not Nullable, Default: False                 | Flag indicating if the user has administrative privileges.                  |

**Relationships:**
- `lesson_progress`: One-to-Many with `UserLessonProgress`. Each user can have progress records for multiple lessons.

---

### 2.2. `Kana`

Stores individual Hiragana and Katakana characters.

| Column              | Type        | Constraints                                  | Description                                                              |
|---------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                | Integer     | Primary Key                                  | Unique identifier for the Kana character.                                |
| `character`         | String(5)   | Not Nullable, Unique                         | The Kana character itself (e.g., "あ", "カ").                               |
| `romanization`      | String(10)  | Not Nullable                                 | Romanized representation (e.g., "a", "ka").                              |
| `type`              | String(10)  | Not Nullable                                 | Type of Kana: 'hiragana' or 'katakana'.                                  |
| `stroke_order_info` | String(255) | Nullable                                     | Information or link to stroke order diagram/animation.                   |
| `example_sound_url` | String(255) | Nullable                                     | URL to an audio file demonstrating pronunciation.                        |

---

### 2.3. `Kanji`

Stores individual Kanji characters with their meanings, readings, and other relevant information.

| Column              | Type        | Constraints                                  | Description                                                              |
|---------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                | Integer     | Primary Key                                  | Unique identifier for the Kanji character.                               |
| `character`         | String(5)   | Not Nullable, Unique                         | The Kanji character itself (e.g., "日", "本").                               |
| `meaning`           | Text        | Not Nullable                                 | English meaning(s) of the Kanji.                                         |
| `onyomi`            | String(100) | Nullable                                     | On'yomi (Chinese reading) of the Kanji.                                  |
| `kunyomi`           | String(100) | Nullable                                     | Kun'yomi (Japanese reading) of the Kanji.                                |
| `jlpt_level`        | Integer     | Nullable                                     | JLPT level associated with the Kanji (e.g., 5 for N5, 1 for N1).         |
| `stroke_order_info` | String(255) | Nullable                                     | Information or link to stroke order diagram/animation.                   |
| `radical`           | String(10)  | Nullable                                     | The main radical of the Kanji.                                           |
| `stroke_count`      | Integer     | Nullable                                     | Number of strokes in the Kanji.                                          |
| `status`            | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`     | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

### 2.4. `Vocabulary`

Stores vocabulary words, including readings, meanings, and example sentences.

| Column                      | Type        | Constraints                                  | Description                                                              |
|-----------------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                        | Integer     | Primary Key                                  | Unique identifier for the vocabulary item.                               |
| `word`                      | String(100) | Not Nullable, Unique                         | The vocabulary word in Japanese (e.g., "猫", "食べる").                      |
| `reading`                   | String(100) | Not Nullable                                 | Hiragana/Katakana reading of the word (e.g., "ねこ", "たべる").              |
| `meaning`                   | Text        | Not Nullable                                 | English meaning(s) of the word.                                          |
| `jlpt_level`                | Integer     | Nullable                                     | JLPT level associated with the vocabulary.                               |
| `example_sentence_japanese` | Text        | Nullable                                     | Example sentence in Japanese using the word.                             |
| `example_sentence_english`  | Text        | Nullable                                     | English translation of the example sentence.                             |
| `audio_url`                 | String(255) | Nullable                                     | URL to an audio file for the word's pronunciation.                       |
| `status`                    | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`             | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

### 2.5. `Grammar`

Stores grammar points, explanations, and example structures.

| Column            | Type        | Constraints                                  | Description                                                                 |
|-------------------|-------------|----------------------------------------------|-----------------------------------------------------------------------------|
| `id`              | Integer     | Primary Key                                  | Unique identifier for the grammar point.                                    |
| `title`           | String(200) | Not Nullable, Unique                         | Title of the grammar point (e.g., "Usage of Particle は").                  |
| `explanation`     | Text        | Not Nullable                                 | Detailed explanation of the grammar rule.                                   |
| `structure`       | String(255) | Nullable                                     | Common structure or pattern for the grammar point (e.g., "Noun + は..."). |
| `jlpt_level`      | Integer     | Nullable                                     | JLPT level associated with the grammar point.                               |
| `example_sentences`| Text        | Nullable                                     | Example sentences demonstrating the grammar point (could be JSON/CSV text). |
| `status`            | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`     | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

## 3. Lesson System Models

### 3.1. `LessonCategory`

Defines categories for organizing lessons.

| Column      | Type        | Constraints                               | Description                                                        |
|-------------|-------------|-------------------------------------------|--------------------------------------------------------------------|
| `id`        | Integer     | Primary Key                               | Unique identifier for the lesson category.                         |
| `name`      | String(100) | Not Nullable, Unique                      | Name of the category (e.g., "Hiragana Basics", "Kanji N5").        |
| `description`| Text        | Nullable                                  | A brief description of the category.                               |
| `color_code`| String(7)   | Default: '#007bff'                        | Hex color code for UI representation of the category.              |
| `created_at`| DateTime    | Default: `datetime.utcnow`                | Timestamp of when the category was created.                        |

**Relationships:**
- `lessons`: One-to-Many with `Lesson`. Each category can have multiple lessons.

---

### 3.2. `Lesson`

Represents a single lesson, containing various content items and metadata.

| Column               | Type        | Constraints                                     | Description                                                               |
|----------------------|-------------|-------------------------------------------------|---------------------------------------------------------------------------|
| `id`                 | Integer     | Primary Key                                     | Unique identifier for the lesson.                                         |
| `title`              | String(200) | Not Nullable                                    | Title of the lesson.                                                      |
| `description`        | Text        | Nullable                                        | A brief description of the lesson.                                        |
| `lesson_type`        | String(20)  | Not Nullable                                    | Type of lesson: 'free' or 'premium'.                                      |
| `category_id`        | Integer     | Foreign Key (`lesson_category.id`)              | ID of the `LessonCategory` this lesson belongs to.                        |
| `difficulty_level`   | Integer     | Nullable                                        | Difficulty rating (e.g., 1-5).                                            |
| `instruction_language`| String(10)  | Not Nullable, Default: 'english'              | Language for explanations/instructions (e.g., 'english', 'german').       |
| `estimated_duration` | Integer     | Nullable                                        | Estimated time to complete the lesson in minutes.                         |
| `order_index`        | Integer     | Default: 0                                      | Order of the lesson within its category or overall list.                  |
| `is_published`       | Boolean     | Default: False                                  | Flag indicating if the lesson is visible to users.                        |
| `thumbnail_url`      | String(255) | Nullable                                        | URL for a lesson cover image.                                             |
| `video_intro_url`    | String(255) | Nullable                                        | URL for an optional introductory video for the lesson.                    |
| `created_at`         | DateTime    | Default: `datetime.utcnow`                      | Timestamp of when the lesson was created.                                 |
| `updated_at`         | DateTime    | Default: `datetime.utcnow`, OnUpdate: `datetime.utcnow` | Timestamp of the last update.                                       |

**Relationships:**
- `category`: Many-to-One with `LessonCategory`.
- `content_items`: One-to-Many with `LessonContent`. A lesson can have multiple content items.
- `prerequisites`: One-to-Many with `LessonPrerequisite` (identifies lessons that must be completed before this one).
- `required_by`: One-to-Many with `LessonPrerequisite` (identifies lessons that have this lesson as a prerequisite).
- `user_progress`: One-to-Many with `UserLessonProgress`. Tracks progress for multiple users on this lesson.
- `pages_metadata`: One-to-Many with `LessonPage`. Stores metadata for each page within the lesson.

---

### 3.3. `LessonPrerequisite`

Defines prerequisite relationships between lessons (join table for a self-referential many-to-many on `Lesson`).

| Column                 | Type    | Constraints                                                              | Description                                                        |
|------------------------|---------|--------------------------------------------------------------------------|--------------------------------------------------------------------|
| `id`                   | Integer | Primary Key                                                              | Unique identifier for the prerequisite relationship.               |
| `lesson_id`            | Integer | Foreign Key (`lesson.id`), Not Nullable                                  | ID of the lesson that has a prerequisite.                          |
| `prerequisite_lesson_id`| Integer | Foreign Key (`lesson.id`), Not Nullable                                  | ID of the lesson that must be completed first.                     |
|                        |         | Unique Constraint (`lesson_id`, `prerequisite_lesson_id`)                  | Ensures a prerequisite is not duplicated for the same lesson.    |

**Relationships:**
- `lesson`: Many-to-One with `Lesson` (the lesson that has prerequisites).
- `prerequisite_lesson`: Many-to-One with `Lesson` (the lesson that is a prerequisite).

---

### 3.4. `LessonPage`

Stores metadata for individual pages within a lesson, allowing for titles and descriptions per page.

| Column        | Type        | Constraints                                           | Description                                            |
|---------------|-------------|-------------------------------------------------------|--------------------------------------------------------|
| `id`          | Integer     | Primary Key                                           | Unique identifier for the lesson page metadata.        |
| `lesson_id`   | Integer     | Foreign Key (`lesson.id`), Not Nullable               | ID of the `Lesson` this page belongs to.               |
| `page_number` | Integer     | Not Nullable                                          | The page number within the lesson.                     |
| `title`       | String(200) | Nullable                                              | Optional title for this page.                          |
| `description` | Text        | Nullable                                              | Optional description for this page.                    |
|               |             | Unique Constraint (`lesson_id`, `page_number`)        | Ensures page numbers are unique within a lesson.       |

**Relationships:**
- `lesson`: Many-to-One with `Lesson`.

---

### 3.5. `LessonContent`

Represents an individual piece of content within a lesson page (e.g., a text block, an image, a specific Kana character, a quiz).

| Column                  | Type        | Constraints                                    | Description                                                                    |
|-------------------------|-------------|------------------------------------------------|--------------------------------------------------------------------------------|
| `id`                    | Integer     | Primary Key                                    | Unique identifier for the lesson content item.                                 |
| `lesson_id`             | Integer     | Foreign Key (`lesson.id`), Not Nullable        | ID of the `Lesson` this content item belongs to.                               |
| `content_type`          | String(20)  | Not Nullable                                   | Type of content ('kana', 'kanji', 'vocabulary', 'grammar', 'text', 'image', 'video', 'audio'). |
| `content_id`            | Integer     | Nullable                                       | Foreign key to `Kana`, `Kanji`, `Vocabulary`, or `Grammar` tables if applicable. |
| `title`                 | String(200) | Nullable                                       | Title for multimedia content (e.g., image caption).                            |
| `content_text`          | Text        | Nullable                                       | Text for 'text' type content.                                                  |
| `media_url`             | String(255) | Nullable                                       | URL for 'image', 'video', 'audio' if not using direct file upload.             |
| `order_index`           | Integer     | Default: 0                                     | Order of this content item within its lesson page.                             |
| `page_number`           | Integer     | Not Nullable, Default: 1                       | The page number within the lesson this content belongs to.                     |
| `is_optional`           | Boolean     | Default: False                                 | Flag indicating if this content item is optional for lesson completion.        |
| `created_at`            | DateTime    | Default: `datetime.utcnow`                     | Timestamp of when the content item was created.                                |
| `file_path`             | String(500) | Nullable                                       | Relative path to an uploaded file (stored in `UPLOAD_FOLDER`).                 |
| `file_size`             | Integer     | Nullable                                       | Size of the uploaded file in bytes.                                            |
| `file_type`             | String(50)  | Nullable                                       | MIME type of the uploaded file.                                                |
| `original_filename`     | String(255) | Nullable                                       | Original name of the uploaded file.                                            |
| `is_interactive`        | Boolean     | Default: False                                 | Flag indicating if this content is an interactive element (e.g., a quiz).      |
| `quiz_type`             | String(50)  | Default: 'standard'                            | Type of quiz ('standard', 'adaptive').                                         |
| `max_attempts`          | Integer     | Default: 3                                     | Maximum attempts allowed for an interactive element.                           |
| `passing_score`         | Integer     | Default: 70                                    | Passing score (percentage) for an interactive element.                         |
| `generated_by_ai`       | Boolean     | Not Nullable, Default: False                   | Flag indicating if this content was generated by AI.                           |
| `ai_generation_details` | JSON        | Nullable                                       | Metadata about the AI generation process (model, timestamp, prompts).          |

**Relationships:**
- `lesson`: Many-to-One with `Lesson`.
- `quiz_questions`: One-to-Many with `QuizQuestion`. If `is_interactive` is true and it's a quiz, this links to its questions.

---

## 4. Quiz System Models

### 4.1. `QuizQuestion`

Stores a single question that can be part of a `LessonContent` item marked as interactive.

| Column            | Type        | Constraints                                          | Description                                                               |
|-------------------|-------------|------------------------------------------------------|---------------------------------------------------------------------------|
| `id`              | Integer     | Primary Key                                          | Unique identifier for the quiz question.                                  |
| `lesson_content_id`| Integer     | Foreign Key (`lesson_content.id`), Not Nullable    | ID of the `LessonContent` item this question belongs to.                  |
| `question_type`   | String(50)  | Not Nullable                                         | Type of question (e.g., 'multiple_choice', 'fill_blank', 'true_false').   |
| `question_text`   | Text        | Not Nullable                                         | The text of the question.                                                 |
| `explanation`     | Text        | Nullable                                             | Explanation for the correct answer, shown after attempting.               |
| `hint`            | Text        | Nullable                                             | A hint to help the user solve the question.                               |
| `difficulty_level`| Integer     | Default: 1                                           | Difficulty level of the question (1-5), used for adaptive quizzes.        |
| `points`          | Integer     | Default: 1                                           | Points awarded for a correct answer.                                      |
| `order_index`     | Integer     | Default: 0                                           | Order of this question within its parent `LessonContent` quiz.            |
| `created_at`      | DateTime    | Default: `datetime.utcnow`                           | Timestamp of when the question was created.                               |

**Relationships:**
- `content`: Many-to-One with `LessonContent`.
- `options`: One-to-Many with `QuizOption`. A question can have multiple options (for multiple choice).
- `user_answers`: One-to-Many with `UserQuizAnswer`. Tracks answers from multiple users to this question.

---

### 4.2. `QuizOption`

Stores a single option for a `QuizQuestion` (primarily for multiple-choice types).

| Column      | Type    | Constraints                                       | Description                                                      |
|-------------|---------|---------------------------------------------------|------------------------------------------------------------------|
| `id`        | Integer | Primary Key                                       | Unique identifier for the quiz option.                           |
| `question_id`| Integer | Foreign Key (`quiz_question.id`), Not Nullable  | ID of the `QuizQuestion` this option belongs to.                 |
| `option_text`| Text    | Not Nullable                                      | The text of the option.                                          |
| `is_correct`| Boolean | Default: False                                    | Flag indicating if this is the correct option.                   |
| `order_index`| Integer | Default: 0                                        | Order of this option within its question.                        |
| `feedback`  | Text    | Nullable                                          | Specific feedback to show if this option is selected.            |

**Relationships:**
- `question`: Many-to-One with `QuizQuestion`.

---

### 4.3. `UserQuizAnswer`

Records a user's answer to a specific `QuizQuestion`.

| Column               | Type     | Constraints                                                       | Description                                                                 |
|----------------------|----------|-------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `id`                 | Integer  | Primary Key                                                       | Unique identifier for the user's answer.                                    |
| `user_id`            | Integer  | Foreign Key (`user.id`), Not Nullable                             | ID of the `User` who answered.                                              |
| `question_id`        | Integer  | Foreign Key (`quiz_question.id`), Not Nullable                    | ID of the `QuizQuestion` being answered.                                    |
| `selected_option_id` | Integer  | Foreign Key (`quiz_option.id`), Nullable                          | ID of the `QuizOption` selected by the user (for multiple choice).          |
| `text_answer`        | Text     | Nullable                                                          | User's text input (for fill-in-the-blank type questions).                   |
| `is_correct`         | Boolean  | Default: False                                                    | Flag indicating if the user's answer was correct.                           |
| `answered_at`        | DateTime | Default: `datetime.utcnow`, OnUpdate: `datetime.utcnow`         | Timestamp of when the answer was last submitted/updated.                    |
| `attempts`           | Integer  | Not Nullable, Default: 0                                          | Number of attempts the user made on this question.                          |
|                      |          | Unique Constraint (`user_id`, `question_id`)                      | Ensures a user has only one answer record per question (updated on new attempt). |

**Relationships:**
- `user`: Many-to-One with `User`.
- `question`: Many-to-One with `QuizQuestion`.
- `selected_option`: Many-to-One with `QuizOption`.

---

## 5. User Progress Models

### 5.1. `UserLessonProgress`

Tracks a user's progress through a specific lesson.

| Column                | Type     | Constraints                                           | Description                                                                     |
|-----------------------|----------|-------------------------------------------------------|---------------------------------------------------------------------------------|
| `id`                  | Integer  | Primary Key                                           | Unique identifier for the progress record.                                      |
| `user_id`             | Integer  | Foreign Key (`user.id`), Not Nullable                 | ID of the `User`.                                                               |
| `lesson_id`           | Integer  | Foreign Key (`lesson.id`), Not Nullable               | ID of the `Lesson`.                                                             |
| `started_at`          | DateTime | Default: `datetime.utcnow`                            | Timestamp when the user first started the lesson.                               |
| `completed_at`        | DateTime | Nullable                                              | Timestamp when the user completed the lesson.                                   |
| `is_completed`        | Boolean  | Default: False                                        | Flag indicating if the user has completed the lesson.                           |
| `progress_percentage` | Integer  | Default: 0                                            | Overall progress percentage (0-100).                                            |
| `time_spent`          | Integer  | Default: 0                                            | Estimated time spent by the user on the lesson in minutes.                      |
| `last_accessed`       | DateTime | Default: `datetime.utcnow`                            | Timestamp of the user's last interaction with the lesson.                       |
| `content_progress`    | Text     | Nullable                                              | JSON string storing completion status of individual `LessonContent` items. Example: `{"content_id_1": true, "content_id_2": false}` |
|                       |          | Unique Constraint (`user_id`, `lesson_id`)            | Ensures one progress record per user per lesson.                                |

**Relationships:**
- `user`: Many-to-One with `User`.
- `lesson`: Many-to-One with `Lesson`.

## 6. Database Migrations

Database schema changes are managed using Alembic. Migration scripts are located in the `migrations/versions/` directory.
- To generate a new migration after model changes: `alembic revision -m "description_of_changes"`
- To apply pending migrations: `python run_migrations.py` (which typically runs `alembic upgrade head`)

The initial schema is created by `db.create_all()` (called via `python setup_unified_auth.py`). Subsequent changes rely on Alembic migrations.
