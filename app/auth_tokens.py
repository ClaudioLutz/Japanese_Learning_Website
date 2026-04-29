# app/auth_tokens.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

_SALT = 'pwd-reset-v1'


def make_reset_token(user_id: int) -> str:
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)
    return s.dumps(int(user_id))


def verify_reset_token(token: str, max_age: int = 3600) -> int | None:
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)
    try:
        return int(s.loads(token, max_age=max_age))
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None
