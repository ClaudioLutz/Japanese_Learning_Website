# app/forms.py
import re  # Import re for regex
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

# Custom validator for password complexity
def password_complexity_validator(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r"[a-z]", password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search(r"[A-Z]", password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r"[0-9]", password):
        raise ValidationError('Password must contain at least one number.')
    if not re.search(r"[!@#$%^&*()-_=+{};:,<.>?~`|]", password): # Added common special characters
        raise ValidationError('Password must contain at least one special character.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), password_complexity_validator])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
