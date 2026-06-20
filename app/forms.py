from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User
import re


class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField(
        'Passwort wiederholen', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    def validate_password(self, password):
        """Mindestens 1 Grossbuchstabe, 1 Kleinbuchstabe und 1 Ziffer."""
        val = password.data
        if not re.search(r'[A-Z]', val):
            raise ValidationError('Passwort muss mindestens einen Grossbuchstaben enthalten.')
        if not re.search(r'[a-z]', val):
            raise ValidationError('Passwort muss mindestens einen Kleinbuchstaben enthalten.')
        if not re.search(r'\d', val):
            raise ValidationError('Passwort muss mindestens eine Ziffer enthalten.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Bitte einen anderen Benutzernamen wählen.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Bitte eine andere E-Mail-Adresse verwenden.')

class LoginForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset-Link senden')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Neues Passwort', validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField(
        'Passwort wiederholen',
        validators=[DataRequired(), EqualTo('password', message='Passwoerter stimmen nicht ueberein.')],
    )
    submit = SubmitField('Passwort speichern')

    def validate_password(self, password):
        val = password.data
        if not re.search(r'[A-Z]', val):
            raise ValidationError('Passwort muss mindestens einen Grossbuchstaben enthalten.')
        if not re.search(r'[a-z]', val):
            raise ValidationError('Passwort muss mindestens einen Kleinbuchstaben enthalten.')
        if not re.search(r'\d', val):
            raise ValidationError('Passwort muss mindestens eine Ziffer enthalten.')


class CSRFTokenForm(FlaskForm):
    """A dummy form for generating a CSRF token."""
    pass


# ── Forum ─────────────────────────────────────────────────────────────────

class TopicForm(FlaskForm):
    """Neues Thema (Topic + Eroeffnungsbeitrag)."""
    title = StringField('Titel', validators=[
        DataRequired(message='Bitte einen Titel eingeben.'),
        Length(min=5, max=200,
               message='Der Titel muss zwischen 5 und 200 Zeichen lang sein.'),
    ])
    body = TextAreaField('Beitrag', validators=[
        DataRequired(message='Bitte einen Text eingeben.'),
        Length(min=10, max=10000,
               message='Der Beitrag muss zwischen 10 und 10 000 Zeichen lang sein.'),
    ])
    submit = SubmitField('Thema erstellen')


class PostForm(FlaskForm):
    """Antwort auf ein Thema bzw. Bearbeiten eines bestehenden Beitrags."""
    body = TextAreaField('Beitrag', validators=[
        DataRequired(message='Bitte einen Text eingeben.'),
        Length(min=2, max=10000,
               message='Der Beitrag muss zwischen 2 und 10 000 Zeichen lang sein.'),
    ])
    submit = SubmitField('Antworten')
