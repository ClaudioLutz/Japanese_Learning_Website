# Japanese Learning Platform

A comprehensive Japanese and German language learning platform built with Flask, PostgreSQL, and Google Cloud. This application leverages AI (OpenAI and Google Gemini) to generate lesson content, provides an interactive learning experience with multimedia support, and includes payment integration for premium content.

## 🌟 Features

*   **Interactive Lessons**: Dynamic lessons with text, audio, images, and videos.
*   **AI-Powered Content Generation**: Automated lesson creation using OpenAI and Google Gemini.
*   **User Authentication**: Secure signup/login with email and Google OAuth support.
*   **Payment Integration**: PostFinance Checkout integration for purchasing courses or premium features.
*   **Admin Interface**: Tools for managing users, courses, and lessons.
*   **Progress Tracking**: Track user progress and completion of lessons.
*   **Multimedia Support**: Handling of images, audio, and video content for lessons.
*   **Responsive Design**: Built for desktop and mobile use.

## 🛠 Technology Stack

*   **Backend**: Python, Flask
*   **Database**: PostgreSQL (Cloud SQL in production)
*   **ORM**: SQLAlchemy
*   **Authentication**: Flask-Login, Python Social Auth (Google OAuth)
*   **AI Services**: OpenAI API, Google Generative AI (Gemini)
*   **Deployment**: Google Cloud Run / Google Compute Engine
*   **Containerization**: Docker
*   **Payments**: PostFinance Checkout

## 🚀 Local Development Setup

### Prerequisites

*   Python 3.12+
*   PostgreSQL
*   Docker (optional, for containerized development)
*   Google Cloud SDK (for deployment)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Create a `.env` file in the root directory. You can use a template or add the following keys:
    ```
    SECRET_KEY=your-secret-key
    WTF_CSRF_SECRET_KEY=your-csrf-secret-key
    DATABASE_URL=postgresql://user:password@localhost/japanese_learning
    OPENAI_API_KEY=your-openai-api-key
    GOOGLE_API_KEY=your-google-api-key
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    ```

5.  **Initialize the Database:**
    ```bash
    flask db upgrade
    # Or run the setup script if available
    ```

6.  **Run the Application:**
    ```bash
    flask run
    ```
    The application will be available at `http://localhost:5000`.

## 📂 Project Structure

*   `app/`: Main application package.
    *   `models.py`: Database models.
    *   `routes.py`: Application routes and views.
    *   `templates/`: HTML templates.
    *   `static/`: Static files (CSS, JS, images).
*   `migrations/`: Database migration files.
*   `lesson_creation_scripts/`: Scripts for generating lesson content using AI.
*   `run.py`: Entry point for the Flask application.
*   `requirements.txt`: Python dependencies.
*   `Dockerfile`: Docker configuration for the application.

## 🤖 AI Content Generation Scripts

The repository includes several scripts for automating the creation of lesson content:

*   `generate_all_lesson_scripts.py`: Generates scripts for lessons.
*   `multimedia_lesson_creator.py`: Creates multimedia assets for lessons.
*   `generate_japanese_lessons_for_germans.py`: Specialized generator for German speakers learning Japanese.
*   `run_lesson_pipeline.py`: Orchestrates the lesson generation process.

## ☁️ Deployment

For deployment instructions, please refer to the following guides included in the repository:

*   [Cloud Run Deployment Guide](CLOUD_RUN_DEPLOYMENT.md): Instructions for deploying to Google Cloud Run.
*   [Google Cloud VM Setup](setup_google_cloud_vm_with_cloud_db.md): Guide for setting up a VM with Cloud SQL.

## 📄 License

[License Information]
