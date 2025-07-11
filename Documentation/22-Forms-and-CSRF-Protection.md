# 22. Forms and CSRF Protection

## 1. Overview

The application uses the **Flask-WTF** extension, which integrates the powerful **WTForms** library, to handle all web form submissions. This system provides a structured and secure way to define, render, validate, and process form data.

A key feature provided by Flask-WTF is built-in protection against Cross-Site Request Forgery (CSRF) attacks, which is enabled by default for all forms.

## 2. CSRF Protection

### 2.1. What is CSRF?
Cross-Site Request Forgery is an attack that tricks a user into submitting a malicious request. It inherits the user's identity and privileges to perform an undesired function on their behalf, such as changing an email address, deleting content, or transferring funds, without their knowledge.

### 2.2. How Flask-WTF Provides Protection
Flask-WTF automatically generates and validates a unique CSRF token for each form submission. The workflow is as follows:

1.  **Token Generation**: For each user session, Flask-WTF generates a unique, cryptographically signed token. This requires the `SECRET_KEY` to be set in the Flask application configuration.
2.  **Token Embedding**: When a form is rendered in a template, a hidden input field containing this CSRF token is added. This is typically done by calling `{{ form.hidden_tag() }}` or `{{ form.csrf_token }}` within the `<form>` tags.
3.  **Token Validation**: When the user submits the form, the submitted CSRF token is compared with the token stored in the user's session. If they do not match, the request is rejected with a 400 Bad Request error, and the form's `validate_on_submit()` method returns `False`.

This ensures that only forms originating from the application's own pages can be successfully submitted, thwarting attacks from malicious external sites.

### 2.3. Configuration
CSRF protection is automatically enabled when you use `FlaskForm`. The only mandatory configuration is setting a strong, secret value for `SECRET_KEY` in your application config.

```python
# In instance/config.py or your main config
SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-and-hard-to-guess-string'
```

## 3. Application Forms

All form classes are defined in `app/forms.py` and inherit from `flask_wtf.FlaskForm`.

### 3.1. `RegistrationForm`
Handles new user registration.

-   **Fields**:
    -   `username`: `StringField`
    -   `email`: `StringField`
    -   `password`: `PasswordField`
    -   `password2`: `PasswordField` (for confirmation)
    -   `submit`: `SubmitField`
-   **Validators**:
    -   `DataRequired()`: Ensures fields are not empty.
    -   `Email()`: Validates the format of the email address.
    -   `EqualTo('password')`: Ensures the password confirmation field matches the password field.
    -   **Custom Validators**:
        -   `validate_username(self, username)`: Queries the database to ensure the username is not already taken.
        -   `validate_email(self, email)`: Queries the database to ensure the email is not already in use.

### 3.2. `LoginForm`
Handles existing user login.

-   **Fields**:
    -   `email`: `StringField`
    -   `password`: `PasswordField`
    -   `remember`: `BooleanField` (for "Remember Me" functionality)
    -   `submit`: `SubmitField`
-   **Validators**:
    -   `DataRequired()`: Ensures email and password are provided.
    -   `Email()`: Validates the email format.

### 3.3. `CSRFTokenForm`
This is a special-purpose, "empty" form used to provide CSRF protection for actions that don't require a full form but still modify state, such as a "delete" button.

-   **Purpose**: To generate a CSRF token that can be included in a simple POST request.
-   **Usage**: An instance of this form can be passed to a template. The template can then render just the hidden CSRF token field inside a minimal form that wraps a button or link. This ensures that even simple actions are protected from CSRF attacks.

**Example Use Case for `CSRFTokenForm`**:
A "Delete Lesson" button in an admin panel.

```html
<!-- In a template -->
<form action="{{ url_for('admin.delete_lesson', lesson_id=lesson.id) }}" method="post" style="display:inline;">
  {{ csrf_form.hidden_tag() }}  <!-- Renders the hidden CSRF token -->
  <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Are you sure you want to delete this lesson?');">
    Delete
  </button>
</form>
```
In the route, you would instantiate `csrf_form = CSRFTokenForm()` and pass it to the template.

## 4. Implementation in Templates

To render a form and its CSRF token correctly, the `form.hidden_tag()` method should be used within the `<form>` element. This method conveniently renders all hidden fields for the form, including the crucial `csrf_token`.

**Example: `login.html`**
```html
<form action="" method="post" novalidate>
    {{ form.hidden_tag() }}
    <p>
        {{ form.email.label }}<br>
        {{ form.email(size=32) }}<br>
        {% for error in form.email.errors %}
        <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </p>
    <p>
        {{ form.password.label }}<br>
        {{ form.password(size=32) }}<br>
        {% for error in form.password.errors %}
        <span style="color: red;">[{{ error }}]</span>
        {% endfor %}
    </p>
    <p>{{ form.remember() }} {{ form.remember.label }}</p>
    <p>{{ form.submit() }}</p>
</form>
