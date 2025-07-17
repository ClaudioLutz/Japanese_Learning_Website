# Project Overview

## Purpose
A comprehensive web-based Japanese learning platform that provides structured lessons for learning Hiragana, Katakana, Kanji, vocabulary, and grammar. The platform features a tiered subscription model with free and premium content access.

## Key Features
- **Unified Authentication System:** Single, secure login for users and administrators with guest access support.
- **Subscription Management:** Supports Free and Premium content access tiers with upgrade/downgrade functionality.
- **Comprehensive Content Management System (CMS):** Full CRUD operations for Kana, Kanji, Vocabulary, and Grammar with AI-powered content generation.
- **Role-Based Access Control (RBAC):** Distinct permissions for student and administrator roles with CSRF protection.
- **Interactive Lesson System:** Multi-page lessons with multimedia, interactive quizzes (multiple choice, fill-in-the-blank, true/false, matching), and flexible content ordering.
- **Course Organization System:** Structured course collections with lesson groupings and progress tracking.
- **User Progress Tracking:** Comprehensive monitoring of lesson completion, quiz performance, and individual content progress.
- **AI-Powered Content Generation:** Advanced AI services for lesson content, explanations, quiz creation, and educational image generation.
- **Lesson Export/Import System:** Complete lesson portability with ZIP packaging for content sharing and backup.
- **File Upload System:** Secure multimedia file handling with validation, processing, and organized storage.
- **Guest Access Support:** Allows non-authenticated users to access selected free content.
- **Content Approval Workflow:** Review and approval system for AI-generated content.
- **Responsive Design:** Optimized experience across desktop, tablet, and mobile devices.

## Target Users

### Students
- **Primary Users**: Individuals learning Japanese language
- **Access Levels**: Free and Premium subscription tiers
- **Features**: 
  - Browse and access lessons based on subscription level
  - Track learning progress through lessons
  - Interactive quiz participation
  - Prerequisite-based learning progression

### Educators
- **Role**: Teachers managing Japanese learning content
- **Capabilities**:
  - Create and manage learning content (Kana, Kanji, Vocabulary, Grammar)
  - Design structured lessons with multimedia content
  - Organize content into categories and learning paths
  - Set lesson prerequisites and difficulty levels

### Administrators
- **Role**: System managers overseeing platform operations
- **Full Access**: Complete administrative control
- **Responsibilities**:
  - User management and role assignment
  - Content moderation and publishing
  - System configuration and maintenance
  - Analytics and performance monitoring

## Core Learning Content Types

### 1. Kana (Hiragana & Katakana)
- Character recognition and pronunciation
- Stroke order information
- Audio pronunciation examples
- Practice exercises and quizzes

### 2. Kanji
- Character meanings and readings (On'yomi, Kun'yomi)
- JLPT level classification
- Stroke order and radical information
- Example usage in context

### 3. Vocabulary
- Japanese words with readings and meanings
- JLPT level organization
- Example sentences in Japanese and English
- Audio pronunciation support

### 4. Grammar
- Grammar rules and patterns
- Detailed explanations and structures
- Example sentences demonstrating usage
- JLPT level categorization

## System Capabilities

### Content Management
- **CRUD Operations:** Full Create, Read, Update, Delete capabilities for all content types (Kana, Kanji, Vocabulary, Grammar).
- **Multimedia Support:** Integration of text, images, videos, and audio via URLs or direct file uploads with comprehensive validation.
- **File Upload System:** Secure handling, storage, and serving of uploaded media files with MIME type validation and image processing.
- **Content Validation:** Advanced validation for uploaded content including file type verification and security checks.
- **AI-Assisted Content Generation:** Comprehensive AI tools for generating lesson content, explanations, quizzes, and educational images.
- **Content Approval Workflow:** Review and approval system for AI-generated content with status tracking.
- **Bulk Operations:** Support for bulk content creation, editing, and deletion operations.
- **Export/Import System:** Complete lesson export to JSON/ZIP format with file packaging for content sharing.

### Lesson System
- **Multi-Page Structure:** Lessons organized into pages with metadata support for titles and descriptions.
- **Flexible Content Ordering:** Drag-and-drop reordering of content within pages and across lesson structure.
- **Interactive Elements:** Multiple quiz types (multiple choice, fill-in-blank, true/false, matching) with adaptive scoring.
- **Progress Tracking:** Detailed monitoring of user progress through lessons, pages, and individual content items.
- **Prerequisites & Categories:** Define lesson dependencies and organize content into color-coded categories.
- **Course Organization:** Group lessons into structured courses with progress tracking and completion metrics.
- **Guest Access:** Configurable guest access for selected free content without authentication.

### Quiz System
- **Multiple Question Types:** Support for multiple choice, fill-in-the-blank, true/false, and matching questions.
- **Adaptive Scoring:** Configurable attempts, passing scores, and progressive hints.
- **Detailed Feedback:** Question-specific explanations and option-level feedback.
- **Progress Integration:** Quiz results integrated with overall lesson progress tracking.
- **AI-Generated Questions:** Automated quiz creation with difficulty adjustment and variety.

### User Experience
- **Responsive Design:** Optimized for seamless experience across desktop, tablet, and mobile devices.
- **Intuitive Navigation:** Clear pathways for lesson discovery, progression, and content interaction.
- **Progress Visualization:** Comprehensive indicators of lesson completion, quiz performance, and overall progress.
- **Guest Support:** Non-authenticated access to selected free content for trial and accessibility.
- **Subscription Management:** Easy upgrade/downgrade between free and premium tiers.

## Technical Architecture
- **Backend Framework:** Python with Flask.
- **Database & ORM:** SQLAlchemy with Flask-SQLAlchemy, using SQLite for development and Alembic for migrations. Production environments can use PostgreSQL/MySQL.
- **Frontend Technologies:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3.
- **Authentication:** Flask-Login for secure session management.
- **Forms:** Flask-WTF with CSRF protection.
- **File Handling:** Pillow for image processing, python-magic for file type identification.

## Deployment Flexibility
- **Development Environment:** Easy local setup using Python virtual environments and SQLite.
- **Production Readiness:** Designed for deployment on various platforms, with considerations for more robust databases like PostgreSQL or MySQL.
- **Configuration:** Managed via environment variables or configuration files.
- **Database Migrations:** Alembic for smooth schema evolution.
