import jwt
import datetime
from django.conf import settings


def generate_access_token(user):
    """Generate a JWT access token for the given user."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRY_MINUTES
        ),
        'iat': datetime.datetime.utcnow(),
        'type': 'access',
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')


def generate_refresh_token(user):
    """Generate a JWT refresh token for the given user."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRY_DAYS
        ),
        'iat': datetime.datetime.utcnow(),
        'type': 'refresh',
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT token. Returns the payload or raises an exception."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
