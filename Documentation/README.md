# Japanese Learning Website - Documentation

## Overview
This documentation provides comprehensive information about the Japanese Learning Website project, a sophisticated educational platform designed for Japanese language learning.

## Documentation Structure

### Core Documentation
- [**01-Executive-Summary.md**](01-Executive-Summary.md) - Project vision, business value, and key metrics
- [**02-Project-Overview.md**](02-Project-Overview.md) - Purpose, features, and target users
- [**03-System-Architecture.md**](03-System-Architecture.md) - High-level architecture and design principles
- [**04-Technology-Stack.md**](04-Technology-Stack.md) - Technologies used and design decisions

### Setup & Configuration
- [**05-Installation-Setup.md**](05-Installation-Setup.md) - Step-by-step installation guide
- [**06-Configuration-Management.md**](06-Configuration-Management.md) - Environment variables and configuration

### System Components
- [**07-User-Authentication.md**](07-User-Authentication.md) - Authentication system, user roles, and API endpoints.
- [**08-Admin-Content-Management.md**](08-Admin-Content-Management.md) - Admin panel and content management functionalities. *(Drafted)*
- [**09-Lesson-System.md**](09-Lesson-System.md) - Architecture of the lesson system, including pages, content types, and progress tracking. *(Drafted)*
- [**10-Database-Schema.md**](10-Database-Schema.md) - Detailed description of database tables, columns, and relationships. *(Drafted)*

### Development & Deployment
- [**11-API-Design.md**](11-API-Design.md) - API endpoint specifications and design patterns. *(Placeholder Drafted)*
- [**12-Frontend-Architecture.md**](12-Frontend-Architecture.md) - Overview of frontend technologies, template structure, and static assets. *(Placeholder Drafted)*
- [**13-File-Structure.md**](13-File-Structure.md) - Project organization and file layout. *(Placeholder Drafted; see also root README.md)*
- [**14-Security-Implementation.md**](14-Security-Implementation.md) - Details on security measures and best practices. *(Placeholder Drafted)*

### Operations & Maintenance
- [**15-Development-Workflow.md**](15-Development-Workflow.md) - Recommended development processes, version control, and coding standards. *(Placeholder Drafted)*
- [**16-Troubleshooting.md**](16-Troubleshooting.md) - Common issues and solutions.
- [**17-Future-Roadmap.md**](17-Future-Roadmap.md) - Planned features and enhancements.
- [**18-AI-Lesson-Creation.md**](18-AI-Lesson-Creation.md) - How the AI lesson creation feature works
- [**19-Lesson-Creation-Scripts.md**](19-Lesson-Creation-Scripts.md) - How to use the lesson creation scripts

## Quick Start
1. Read the [Project Overview](02-Project-Overview.md) to understand the system.
2. Follow the [Installation Guide](05-Installation-Setup.md) to set up your development environment.
3. Review the [System Architecture](03-System-Architecture.md) to understand the codebase structure.
4. Check the [Troubleshooting Guide](16-Troubleshooting.md) if you encounter issues.

## Key Features

The platform offers a comprehensive suite of features for Japanese language education:

- **Unified Authentication System:** Secure and single login for both users and administrators, built with Flask-Login.
- **Subscription Management:** Supports different access levels with Free and Premium tiers.
- **Comprehensive Content Management System (CMS):** Administrators have full CRUD (Create, Read, Update, Delete) capabilities for all learning materials, including:
    - Kana (Hiragana & Katakana)
    - Kanji (Characters, readings, meanings, JLPT levels)
    - Vocabulary (Words, readings, meanings, example sentences)
    - Grammar (Rules, explanations, examples)
- **Interactive Lesson System:**
    - **Structured & Paginated Lessons:** Organize content into multiple pages with a clear flow.
    - **Multimedia Support:** Integrate text, images, videos, and audio (URL-based or direct uploads).
    - **Interactive Quizzes:** Multiple choice, fill-in-the-blank, and true/false questions.
    - **Content Ordering:** Flexible arrangement of items within lesson pages.
    - **Carousel Navigation:** User-friendly swipe navigation for lesson pages.
- **User Progress Tracking:** Detailed monitoring of individual student progress, including lesson and page completion.
- **Role-Based Access Control (RBAC):** Distinct permissions for user and administrator roles.
- **AI-Powered Lesson Creation:** Tools to assist administrators in generating lesson content using AI.
- **Scripted Lesson Creation:** Utilities for bulk creation of specific lesson types.
- **Lesson Prerequisites:** Define dependencies between lessons for structured learning paths.
- **Categories & Organization:** Color-coded categories for easy lesson discovery.
- **Time Monitoring:** Track time spent on lessons.

## Technology Stack

The project leverages a modern and robust technology stack:

- **Backend:** Python with the Flask framework.
- **Database:** SQLite for development (easily upgradeable to PostgreSQL, MySQL, or other relational databases for production).
    - **ORM:** SQLAlchemy with Flask-SQLAlchemy for database interactions.
    - **Migrations:** Alembic for managing database schema changes.
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), and Bootstrap 5.3.3 for responsive design.
- **Authentication:** Flask-Login for managing user sessions and authentication.
- **Forms:** Flask-WTF for secure web form handling and CSRF protection.
- **File Processing:** Pillow for image manipulation and python-magic for identifying file types (enhancing security for uploads).
- **AI Integration:** (Specify libraries if known, e.g., OpenAI API client) - *Covered in `18-AI-Lesson-Creation.md`*

## Support
For questions, issues, or contributions, please refer to the relevant documentation sections or contact the development team.
