# Model Development & Implementation Documentation

## 1. Overview

This document provides a comprehensive overview of the model development and implementation for the Japanese Learning Website. The platform is a sophisticated, AI-enhanced educational tool designed for Japanese language learners. It features a robust backend, a comprehensive content management system, and advanced AI-powered features for lesson and quiz generation.

This document covers the system's architecture, technology stack, database schema, data models, and the core components of its AI and security infrastructure.

### Table of Contents
1.  [Overview](#1-overview)
2.  [System Architecture](#2-system-architecture)
3.  [Technology Stack](#3-technology-stack)
4.  [Database Schema and Data Models](#4-database-schema-and-data-models)
5.  [AI Content Generation System](#5-ai-content-generation-system)
6.  [Frontend and User Interface](#6-frontend-and-user-interface)
7.  [Security](#7-security)
8.  [Deployment and Operations](#8-deployment-and-operations)

## 2. System Architecture

The Japanese Learning Website is built using a **layered monolithic architecture**. This design provides a clear separation of concerns, making the application maintainable and scalable. The architecture is based on the **Model-View-Controller (MVC)** pattern, which is well-suited for a Flask environment.

### Core Design Principles

*   **Separation of Concerns:** The application is divided into distinct components, each with a specific responsibility:
    *   **Models (`app/models.py`):** Define the data structure, relationships, and business logic.
    *   **Views (`app/templates/`):** Handle the presentation logic using Jinja2 templates.
    *   **Controllers (`app/routes.py`):** Manage the application flow, handle HTTP requests, and interact with the models and views.
    *   **Services (`app/ai_services.py`, `app/utils.py`):** Encapsulate specific functionalities like AI content generation and file uploads.

*   **Single Responsibility Principle:** Each module and class has a single, well-defined responsibility. For example, the `User` model is responsible for user-related data and authentication, while the `AILessonContentGenerator` is responsible for all AI-related content generation.

*   **Application Factory:** The application uses the application factory pattern (`create_app` in `app/__init__.py`), which allows for flexible configuration and improved testability.

*   **Security by Design:** Security is a core consideration in the architecture, with features like role-based access control (RBAC), CSRF protection, and secure file handling built into the application's design.

## 3. Technology Stack

The project leverages a modern and robust technology stack, chosen to balance performance, scalability, and ease of development.

### Backend Technologies

*   **Python:** The core programming language, chosen for its readability, extensive libraries, and strong community support.
*   **Flask:** A lightweight and flexible web framework that provides the foundation for the application.
*   **SQLAlchemy:** A powerful Object-Relational Mapper (ORM) that simplifies database interactions and allows for complex queries and relationships.
*   **Flask-Login:** Manages user authentication and session management.
*   **Flask-WTF:** Handles form creation, validation, and CSRF protection.
*   **OpenAI API:** Used for AI-powered content generation, including text, quizzes, and images.

### Frontend Technologies

*   **HTML5, CSS3, JavaScript:** The standard technologies for building the user interface.
*   **Bootstrap:** A responsive UI framework that provides a consistent look and feel and accelerates frontend development.
*   **Jinja2:** A server-side templating engine that allows for dynamic rendering of HTML pages.

### Database

*   **PostgreSQL:** A robust and scalable relational database used for the production environment.
*   **SQLite:** A lightweight, file-based database used for development and testing.
*   **Alembic:** A database migration tool that manages schema changes over time.

## 4. Database Schema and Data Models

The database is the backbone of the application, storing all user data, content, and progress. The schema is designed to be relational and normalized, ensuring data integrity and minimizing redundancy.

### Core Models

*   **User:** Stores user information, including authentication details, subscription level, and admin status.
*   **Kana:** Stores individual Hiragana and Katakana characters with their romanization and type.
*   **Kanji:** Stores individual Kanji characters with their meanings, readings, and JLPT level.
*   **Vocabulary:** Stores vocabulary words with their readings, meanings, and example sentences.
*   **Grammar:** Stores grammar points with explanations and example structures.

### Lesson System Models

*   **LessonCategory:** Defines categories for organizing lessons, each with a name, description, and color code.
*   **Lesson:** Represents a single lesson with a title, description, type, and other metadata. It has relationships with content items, prerequisites, and user progress.
*   **LessonPrerequisite:** Defines prerequisite relationships between lessons.
*   **LessonPage:** Stores metadata for individual pages within a lesson.
*   **LessonContent:** Represents a single piece of content within a lesson, such as text, an image, or a quiz.

### Quiz System Models

*   **QuizQuestion:** Stores a single quiz question with its type, text, and explanation.
*   **QuizOption:** Stores a single option for a multiple-choice question.
*   **UserQuizAnswer:** Records a user's answer to a specific quiz question.

### User Progress Models

*   **UserLessonProgress:** Tracks a user's progress through a specific lesson, including completion status and time spent.

### Course System Models

*   **Course:** Represents a collection of lessons organized into a structured learning path.
*   **course_lessons (Association Table):** A many-to-many table that links courses and lessons.

### Monetization Models

*   **LessonPurchase:** Tracks individual lesson purchases by users.
*   **CoursePurchase:** Tracks individual course purchases by users.
*   **PaymentTransaction:** Records payment transactions and their status.

### Social Authentication Models

*   **social_auth_usersocialauth:** Links users to their social media accounts.
*   **social_auth_nonce, social_auth_association, social_auth_code:** Tables used by the `python-social-auth` library to manage OAuth flows.

## 5. AI Content Generation System

The AI Content Generation system is a central feature of the application, designed to automate and enhance the creation of educational content. It is built around the `AILessonContentGenerator` service class, which is located in `app/ai_services.py`.

### The `AILessonContentGenerator` Service

This class is the heart of the AI system. It provides a suite of methods for generating various types of content, from simple text explanations to complex, structured quizzes and database entries. The service uses the OpenAI API (GPT-4 and DALL-E 3) to perform the actual content generation.

### Key Generation Methods

*   **`generate_explanation` and `generate_formatted_explanation`:** Generate plain text or HTML-formatted explanations on a given topic.
*   **Quiz Generation Methods:** A variety of methods for generating different types of quizzes, including:
    *   `generate_true_false_question`
    *   `generate_fill_in_the_blank_question`
    *   `generate_multiple_choice_question`
    *   `generate_matching_question`
    *   `create_adaptive_quiz`
*   **Database Content Generation:** Methods for generating structured data that can be directly inserted into the database:
    *   `generate_kanji_data`
    *   `generate_vocabulary_data`
    *   `generate_grammar_data`
*   **Image Generation:** Methods for generating images using DALL-E 3:
    *   `generate_image_prompt`
    *   `generate_single_image`
    *   `generate_lesson_images`

## 6. Frontend and User Interface

The frontend of the application is built with a focus on simplicity, responsiveness, and ease of use.

*   **Server-Side Rendering:** The application uses Jinja2 for server-side rendering of HTML, which is well-suited for a content-heavy educational platform.
*   **Bootstrap:** The user interface is built with Bootstrap, which provides a responsive grid system and a consistent set of UI components.
*   **Vanilla JavaScript:** Client-side interactivity is handled with vanilla JavaScript, which keeps the frontend lightweight and avoids the complexity of a large JavaScript framework.

## 7. Security

Security is a key consideration in the design and implementation of the application. The following are some of the key security features:

*   **Authentication:** User authentication is handled by Flask-Login, which provides secure session management. The application also supports social authentication via Google OAuth.
*   **Authorization:** Role-based access control (RBAC) is used to restrict access to certain parts of the application based on user roles (e.g., admin, premium user).
*   **CSRF Protection:** Flask-WTF is used to protect against Cross-Site Request Forgery (CSRF) attacks.
*   **Secure File Uploads:** The application has a robust file upload system that validates file types, sanitizes filenames, and stores files in a secure location.
*   **Password Hashing:** User passwords are securely hashed using Werkzeug's password hashing utilities.
*   **XSS Prevention:** Jinja2's auto-escaping feature is used to prevent Cross-Site Scripting (XSS) attacks.
