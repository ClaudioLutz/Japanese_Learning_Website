# User Authentication System

The Japanese Learning Website employs a unified authentication system for both regular users and administrators, leveraging Flask-Login for session management and custom logic for role-based access control.

## Authentication Flow

### 1. User Registration (`/register` route, `RegistrationForm`)
- New users provide a username, email, and password.
- The system checks for unique username and email (`User.validate_username`, `User.validate_email`).
- Passwords are securely hashed using `werkzeug.security.generate_password_hash` (PBKDF2) before being stored in the `user.password_hash` field.
- Upon successful registration, a new `User` record is created with `subscription_level` defaulting to 'free' and `is_admin` defaulting to `False`.

### 2. User Login (`/login` route, `LoginForm`)
- Users log in with their email and password.
- The system retrieves the user by email and verifies the password using `user.check_password(password)`.
- If credentials are valid, `flask_login.login_user(user)` is called, establishing a secure session.
- A "Remember Me" option allows for persistent sessions.
- Upon successful login, users are redirected:
    - Administrators (`user.is_admin == True`) are redirected to the admin dashboard (`/admin`).
    - Regular users are redirected to the homepage (`/`) or their intended page (`next_page`).

### 3. Session Management (Flask-Login)
- Flask-Login handles user sessions using secure cookies.
- The `@login_required` decorator protects routes that require an authenticated user.
- The `current_user` proxy from Flask-Login provides access to the logged-in user object in views and templates.
- A user loader function (`load_user(user_id)` in `app/models.py`) is registered with Flask-Login to reload the user object from the user ID stored in the session.

### 4. Logout (`/logout` route)
- `flask_login.logout_user()` clears the user session and removes the user from being logged in.

### 5. Role Assignment and Access Control
- **User Roles:**
    - `User.subscription_level`: Determines content access ('free' or 'premium').
    - `User.is_admin`: A boolean flag (`True`/`False`) grants administrative privileges.
- **Access Control Decorators (`app/routes.py`):**
    - `@login_required`: Ensures the user is logged in.
    - `@admin_required`: Ensures `current_user.is_admin` is `True`.
    - `@premium_required`: Ensures `current_user.subscription_level` is 'premium'. (Currently, subscription changes are simulated via prototype routes `/upgrade_to_premium` and `/downgrade_from_premium`).
- Content and feature access within routes and templates is further controlled by checking `current_user.is_admin` and `current_user.subscription_level`.

## User Roles & Permissions Summary

### 1. Standard Users (Free Tier - `subscription_level='free'`)
- **Authentication**: Can register and log in.
- **Content Access**: Access to lessons and content marked as 'free'.
- **Account Management**: Can potentially upgrade to premium (prototype functionality).
- **Permissions**: Cannot access admin panel or premium content.

### 2. Premium Users (Premium Tier - `subscription_level='premium'`)
- **Authentication**: Can register and log in.
- **Content Access**: Access to both 'free' and 'premium' lessons and content.
- **Account Management**: Can potentially downgrade to free (prototype functionality).
- **Permissions**: Cannot access admin panel.

### 3. Administrators (`is_admin=True`)
- **Authentication**: Log in via the standard `/login` route.
- **Content Access**: Full access to all user-facing content (implicitly, as admin checks often supersede subscription checks for admin panel functionality).
- **Admin Panel Access**: Full access to the admin panel (`/admin` and its sub-routes) for managing:
    - Kana, Kanji, Vocabulary, Grammar content.
    - Lesson Categories.
    - Lessons (including creating pages, adding/ordering content, managing prerequisites, publishing).
    - Uploading files for lessons.
    - Creating interactive quiz content.
- **Permissions**: Can perform all CRUD operations on content and lessons. User management capabilities (e.g., directly modifying other users' roles or details) are not explicitly detailed in the current admin routes but could be a future enhancement.

## Security Aspects

### Password Hashing
- Werkzeug's `generate_password_hash` (PBKDF2 with salt) is used to securely store passwords.
- Password verification uses `check_password_hash` for secure comparison.
- Passwords are never stored in plaintext.

### Session Cookies
- Flask-Login uses cryptographically signed cookies to maintain session integrity.
- The `SECRET_KEY` from the application configuration is crucial for this.
- Sessions can be configured for different lifetimes and security levels.

### CSRF Protection
- Flask-WTF is integrated, providing CSRF protection for all form submissions.
- Standard forms (`RegistrationForm`, `LoginForm`) automatically include CSRF tokens.
- Actions like subscription changes (`/upgrade_to_premium`, `/downgrade_from_premium`) and lesson progress reset (`/lessons/<id>/reset`) use a `CSRFTokenForm` to ensure these POST requests are protected even without other form data.

### Route Protection
- Decorators (`@login_required`, `@admin_required`, `@premium_required`) prevent unauthorized access to routes.
- Custom decorators provide fine-grained access control based on user attributes.

## Authentication Implementation Details

### User Model (`app/models.py`)
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    subscription_level = db.Column(db.String(50), default='free', nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def load_user(user_id):
        """User loader function for Flask-Login"""
        return User.query.get(int(user_id))
```

### Access Control Decorators
```python
def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    """Decorator to require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login'))
        if current_user.subscription_level != 'premium':
            flash('Premium subscription required.', 'error')
            return redirect(url_for('routes.upgrade_to_premium'))
        return f(*args, **kwargs)
    return decorated_function
```

### Form Validation
```python
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=20)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6)
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), 
        EqualTo('password')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')
```

## Session Management

### Session Configuration
- **Session Lifetime**: Configurable session timeout
- **Remember Me**: Optional persistent sessions
- **Security**: Secure cookie flags in production
- **Cross-Site Protection**: SameSite cookie attributes

### Session Security
```python
# Production session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)
```

## User Management Features

### Account Creation
- Email validation and uniqueness checking
- Username validation and uniqueness checking
- Password strength requirements
- Automatic role assignment (default: free user)

### Profile Management
- Users can update their profile information
- Password change functionality
- Email verification (future enhancement)
- Account deletion (future enhancement)

### Subscription Management
- Upgrade to premium subscription
- Downgrade to free subscription
- Subscription status tracking
- Access level enforcement

## Authentication API Endpoints

### Public Endpoints
- `GET /login` - Display login form
- `POST /login` - Process login credentials
- `GET /register` - Display registration form
- `POST /register` - Process user registration
- `GET /logout` - Log out current user

### Protected Endpoints
- `POST /upgrade_to_premium` - Upgrade user subscription
- `POST /downgrade_from_premium` - Downgrade user subscription

## Security Best Practices

### Password Security
- Minimum password length requirements
- Password hashing with salt
- Protection against timing attacks
- Password change functionality

### Session Security
- Secure session cookie configuration
- Session timeout management
- Protection against session fixation
- CSRF token validation

### Access Control
- Role-based access control (RBAC)
- Principle of least privilege
- Route-level protection
- Template-level access control

## Future Enhancements

### Planned Authentication Features
- **Two-Factor Authentication**: SMS or app-based 2FA
- **Social Login**: OAuth integration (Google, Facebook)
- **Email Verification**: Account activation via email
- **Password Reset**: Secure password recovery
- **Account Lockout**: Protection against brute force attacks
- **Audit Logging**: Track authentication events
- **Advanced Roles**: More granular permission system

### Security Improvements
- **Rate Limiting**: Login attempt throttling
- **IP Whitelisting**: Admin access restrictions
- **Device Management**: Trusted device tracking
- **Session Analytics**: Login pattern analysis
