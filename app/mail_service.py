# app/mail_service.py
import logging
from flask import render_template
from flask_mail import Mail, Message

mail = Mail()

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_link: str, username: str | None = None) -> bool:
    """Sendet die Passwort-Reset-Mail. Gibt True bei Erfolg zurueck.

    Faengt SMTP-Fehler ab und loggt sie, damit der Request nicht crasht
    und keine Information an den Benutzer leakt (Enumeration-Schutz).
    """
    try:
        subject = 'Passwort zuruecksetzen — Japanese Learning'
        html = render_template(
            'email/reset_password.html',
            reset_link=reset_link,
            username=username or '',
        )
        text = render_template(
            'email/reset_password.txt',
            reset_link=reset_link,
            username=username or '',
        )
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=text,
            html=html,
        )
        mail.send(msg)
        return True
    except Exception:
        logger.exception('Konnte Passwort-Reset-Mail an %s nicht senden', to_email)
        return False
