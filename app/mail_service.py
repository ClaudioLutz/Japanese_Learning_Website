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


def send_issue_resolved_email(
    to_email: str, issue_title: str, issue_url: str,
    reply_text: str | None = None, username: str | None = None,
) -> bool:
    """Benachrichtigt den Melder, dass sein Hinweis bearbeitet wurde.

    Best-effort: faengt SMTP-Fehler ab, damit der Resolve-Request nie crasht.
    Text-only (kein HTML-Template). Gibt True bei Erfolg zurueck.
    """
    try:
        greeting = f'Hallo {username},' if username else 'Hallo,'
        lines = [
            greeting,
            '',
            f'dein Hinweis „{issue_title}" wurde bearbeitet und als erledigt markiert.',
        ]
        if reply_text:
            lines += ['', 'Antwort vom Team:', reply_text]
        lines += [
            '',
            f'Zum Hinweis: {issue_url}',
            '',
            'Danke fuers Mithelfen!',
            'Japanese Learning',
        ]
        msg = Message(subject='Dein Hinweis wurde bearbeitet — Japanese Learning',
                      recipients=[to_email], body='\n'.join(lines))
        mail.send(msg)
        return True
    except Exception:
        logger.exception('Konnte Issue-Resolved-Mail an %s nicht senden', to_email)
        return False


def send_new_issue_admin_email(
    admin_emails, issue_title: str, issue_url: str,
    reporter: str, content_label: str | None = None,
) -> bool:
    """Benachrichtigt das Team ueber einen neuen Hinweis. Best-effort, text-only."""
    recipients = [e for e in (admin_emails or []) if e]
    if not recipients:
        return False
    try:
        lines = [f'Neuer Hinweis von {reporter}:', '', issue_title]
        if content_label:
            lines += ['', f'Betrifft: {content_label}']
        lines += ['', f'Zum Hinweis: {issue_url}']
        msg = Message(subject=f'Neuer Hinweis: {issue_title}',
                      recipients=recipients, body='\n'.join(lines))
        mail.send(msg)
        return True
    except Exception:
        logger.exception('Konnte New-Issue-Admin-Mail nicht senden')
        return False
