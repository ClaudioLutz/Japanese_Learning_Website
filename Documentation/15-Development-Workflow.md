# Development Workflow

## 1. Overview

This document outlines the recommended development workflow for contributing to the Japanese Learning Website project. Following these guidelines helps maintain code quality, consistency, and collaboration efficiency.

## 2. Environment Setup

1.  **Prerequisites**: Ensure Python 3.8+, pip, Git, and virtual environment tools are installed.
2.  **Clone Repository**: `git clone <repository-url>`
3.  **Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```
4.  **Install Dependencies**: `pip install -r requirements.txt`
5.  **Configuration**: Create a `.env` file in the project root with necessary environment variables (see `06-Configuration-Management.md`).
    ```env
    FLASK_APP=run.py
    FLASK_ENV=development
    FLASK_DEBUG=True
    SECRET_KEY=your-dev-secret-key
    DATABASE_URL=sqlite:///instance/site.db
    UPLOAD_FOLDER=app/static/uploads
    OPENAI_API_KEY=your-openai-api-key # If working on AI features
    ```
6.  **Database Setup**:
    ```bash
    python setup_unified_auth.py   # Initializes DB schema and default admin
    python migrate_lesson_system.py # Seeds initial data and runs core data migrations
    # python run_migrations.py     # Apply any pending Alembic migrations if updating an existing setup
    ```

## 3. Version Control (Git)

-   **Branching Strategy**:
    -   `main` (or `master`): Stable, production-ready code. Direct commits are generally disallowed.
    -   `develop`: Integration branch for features that are ready for the next release.
    -   **Feature Branches**: Create new branches from `develop` for each new feature or bugfix (e.g., `feature/new-quiz-type`, `bugfix/login-error`).
        -   Naming: `feature/<short-description>`, `bugfix/<short-description>`, `chore/<task-description>`.
-   **Commits**:
    -   Make small, logical commits.
    -   Write clear and concise commit messages (e.g., imperative mood: "Add user profile page", "Fix validation for email field").
    -   Reference issue numbers if applicable (e.g., "Fix #123: Resolve login redirect loop").
-   **Pull Requests (PRs)**:
    -   When a feature/bugfix is complete, push the branch to the remote repository and open a PR against `develop`.
    -   Provide a clear description of the changes in the PR.
    -   Ensure any relevant tests pass (see Section 5).
    -   Code review by at least one other developer is recommended before merging.
-   **Keeping Up-to-Date**: Regularly pull changes from the remote `develop` branch into your feature branch to avoid large merge conflicts:
    ```bash
    git checkout develop
    git pull origin develop
    git checkout your-feature-branch
    git merge develop
    ```
    Or, use `git rebase develop` for a cleaner history (advanced).

## 4. Coding Standards & Conventions

-   **Python**: Follow PEP 8 style guidelines.
    -   Use a linter (e.g., Flake8, Pylint) and a formatter (e.g., Black, autopep8) to maintain consistency.
-   **Flask**: Adhere to Flask best practices (e.g., using Blueprints for route organization if the app grows, application factory pattern).
-   **HTML/CSS/JavaScript**: Maintain readability and consistency. Comment complex code.
-   **Documentation**:
    -   Add/update relevant project documentation in the `Documentation/` folder for new features or significant changes.
    -   Write clear docstrings for Python functions, classes, and modules.
    -   Comment code where the logic is not immediately obvious.

## 5. Testing

*(While specific test files were not detailed in the initial exploration, a testing strategy is crucial.)*

-   **Unit Tests**:
    -   Focus on testing individual functions, methods, and classes in isolation.
    -   Use a testing framework like `pytest` or Python's built-in `unittest`.
    -   Mock external dependencies (e.g., database, OpenAI API) where appropriate.
    -   Aim for good code coverage.
-   **Integration Tests**:
    -   Test interactions between different components (e.g., route handlers interacting with database models).
    -   Can also use `pytest` or `unittest` with Flask's test client.
-   **End-to-End (E2E) Tests**: (Optional, for larger features)
    -   Use tools like Selenium or Playwright to simulate user interactions in a browser.
-   **Running Tests**:
    -   Establish a command to run all tests (e.g., `pytest`, `python -m unittest discover`).
    -   Tests should be runnable locally and in CI/CD pipelines.
-   **Test-Driven Development (TDD)**: Consider writing tests before writing implementation code, especially for new features.

## 6. Database Migrations (Alembic)

-   When making changes to SQLAlchemy models in `app/models.py` that affect the database schema:
    1.  **Generate a new migration script**:
        ```bash
        alembic revision -m "Descriptive message for schema changes"
        ```
    2.  **Review and Edit**: Carefully inspect the generated script in `migrations/versions/`. Manually adjust if Alembic's autogenerate didn't capture the intent perfectly (especially for constraints, data type changes, or data migrations).
    3.  **Apply the migration locally**:
        ```bash
        python run_migrations.py
        ```
    4.  **Commit the migration script** along with your model changes.
-   **Never manually edit the database schema** in a development or production environment that is managed by Alembic. All changes should go through migration scripts.

## 7. Debugging

-   Utilize Flask's built-in debugger (enabled when `FLASK_DEBUG=True`).
-   Use `print()` statements or Python's `logging` module for more persistent debugging information.
-   Use your IDE's debugging tools.
-   Inspect database state directly using `sqlite3 instance/site.db` or a DB browser.

## 8. Dependency Management

-   Add new Python dependencies to `requirements.txt`.
    ```bash
    pip freeze > requirements.txt # After installing a new package
    ```
-   Regularly review and update dependencies to their latest stable versions to incorporate security patches and improvements.

## 9. Contribution Workflow Summary

1.  Ensure your local `develop` branch is up-to-date: `git checkout develop && git pull origin develop`.
2.  Create a new feature branch: `git checkout -b feature/my-new-feature develop`.
3.  Implement changes, write tests, and add/update documentation.
4.  Commit changes frequently with clear messages.
5.  If database models changed, create and commit Alembic migration scripts.
6.  Run tests locally to ensure they pass.
7.  Push your feature branch to the remote: `git push origin feature/my-new-feature`.
8.  Open a Pull Request against the `develop` branch.
9.  Participate in code review and address feedback.
10. Once approved and tests pass in CI (if applicable), the PR is merged into `develop`.

## 10. Communication

-   Use project management tools (e.g., Jira, Trello, GitHub Issues) to track tasks and bugs.
-   Communicate with team members about ongoing work, potential blockers, and design decisions.

*(This document provides general guidelines. Specific project teams may have additional or slightly different conventions.)*
