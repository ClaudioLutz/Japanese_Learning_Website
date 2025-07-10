# Frontend Architecture

## 1. Overview

The frontend of the Japanese Learning Website is primarily built using server-side rendered HTML templates via Jinja2, styled with Bootstrap 5.3.3, and enhanced with vanilla JavaScript for client-side interactivity and AJAX calls.

## 2. Core Technologies

-   **HTML5**: Semantic markup for structuring content.
-   **CSS3**: Custom styling in conjunction with Bootstrap.
    -   Custom styles are located in `app/static/css/custom.css`.
-   **Bootstrap 5.3.3**: Responsive CSS framework for layout, components (modals, carousels, forms), and overall styling. Typically loaded via CDN.
-   **Jinja2**: Python templating engine used by Flask to render dynamic HTML pages by embedding data from the backend into templates.
-   **JavaScript (ES6+)**: Vanilla JavaScript is used for:
    -   Client-side form validation (though primarily handled server-side by WTForms).
    -   DOM manipulation for UI updates without full page reloads.
    -   AJAX requests to backend API endpoints (e.g., for submitting quiz answers, updating progress, AI content generation in admin panel).
    -   Event handling (e.g., button clicks, carousel interactions).

## 3. Template Structure (`app/templates/`)

-   **Base Templates**:
    -   `base.html`: Main base template for user-facing pages. Includes common structure like navbar, footer, and blocks for content, scripts, and styles.
    -   `admin/base_admin.html`: Base template for admin panel pages, extending `base.html` or providing its own structure with admin-specific navigation.
-   **Layout Inheritance**: Jinja2's template inheritance (`{% extends %}`, `{% block %}`) is used extensively to maintain a consistent layout and reduce code duplication.
-   **User-Facing Pages**:
    -   `index.html`: Homepage.
    -   `lessons.html`: Lists available lessons.
    -   `lesson_view.html`: Displays a single lesson with its paginated content (often using a carousel).
    -   `login.html`, `register.html`: Authentication pages.
-   **Admin Pages (`app/templates/admin/`)**:
    -   `admin_index.html`: Admin dashboard.
    -   `manage_lessons.html`, `manage_categories.html`, etc.: Pages for CRUD operations on different content types.
    -   Forms for creating and editing content are rendered here.
-   **Includes/Macros**: Reusable template snippets (e.g., for rendering a single lesson card, a form field) might be defined using `{% include %}` or Jinja2 macros.

## 4. Static Assets (`app/static/`)

-   **CSS (`app/static/css/`)**: Contains custom stylesheets like `custom.css` that override or supplement Bootstrap styles.
-   **JavaScript (`app/static/js/`)**: (If any custom global JS files exist, they would be here). Much of the JS might be inline in templates or specific to admin panel sections.
-   **Images (`app/static/images/`)**: Site-wide images like logos, backgrounds.
-   **Uploads (`app/static/uploads/`)**: Default directory for user-uploaded content (lesson images, audio). This path is configurable. Files here are served via a dedicated route.

## 5. Key Frontend Components & Interactions

### 5.1. Lesson Display (`lesson_view.html`)
-   Often uses a Bootstrap Carousel component to display lesson pages.
-   JavaScript handles navigation between pages (next/previous buttons, possibly swipe gestures if a library is used).
-   Content items within a page are rendered based on their type.
-   Interactive elements (quizzes) use JavaScript to handle answer submission via AJAX and display feedback.

### 5.2. Admin Panel Forms
-   Forms are generated using Flask-WTF and rendered by Jinja2.
-   Client-side JavaScript might be used for:
    -   Dynamic form elements (e.g., adding more options to a quiz question).
    -   AJAX submissions for parts of the form (e.g., AI content generation, file uploads).
    -   Rich Text Editors (if integrated) for text content.

### 5.3. AJAX Communication
-   Vanilla JavaScript's `fetch` API is used for making asynchronous requests to backend API endpoints.
-   Requests typically send/receive JSON data.
-   CSRF tokens (if required by the endpoint) are included in request headers.
-   Responses are used to update the DOM dynamically (e.g., show success/error messages, refresh parts of a page).

## 6. State Management

-   Primarily stateless from the frontend perspective for page loads (data comes from the backend with each request).
-   Client-side JavaScript may hold temporary UI state (e.g., current page in a lesson carousel, form data before submission).
-   User session state is managed server-side by Flask-Login.

## 7. Build Process / Dependencies

-   No complex frontend build process (e.g., Webpack, Parcel) is implied by the current structure.
-   Frontend dependencies (like Bootstrap) are mainly included via CDNs or are simple static files.

## 8. Future Considerations / Potential Enhancements

-   **JavaScript Framework/Library**: For more complex client-side interactions or a Single Page Application (SPA) feel, a framework like Vue.js, React, or a library like HTMX could be introduced.
-   **Frontend Build Tools**: If JS/CSS complexity grows, tools like Webpack or Parcel could be added for bundling, minification, and transpilation.
-   **State Management Libraries**: For SPAs, client-side state management libraries (e.g., Pinia for Vue, Redux for React) might become necessary.
-   **Improved Asset Management**: More sophisticated handling of static assets.

*(This document is a placeholder and provides a high-level overview based on common Flask frontend practices and inferred project structure. It will be expanded as more specific frontend details are defined or implemented.)*
