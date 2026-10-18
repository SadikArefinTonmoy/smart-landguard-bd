"""Argon2id credentials, revocable HttpOnly sessions and origin-bound CSRF challenges."""
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

from argon2 import PasswordHasher, exceptions as argon_errors
from flask import current_app, g, jsonify, request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import audit, connect, utcnow

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
COOKIE_SESSION = 'lg_session'
COOKIE_CSRF = 'lg_csrf_challenge'
SESSION_HOURS = 8
CSRF_MAX_AGE_SECONDS = 2 * 3600

def sha(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()

def allowed_origins():
    return [s.strip().rstrip('/') for s in os.getenv(
        'LANDGUARD_ALLOWED_ORIGINS', 'http://localhost:4173,http://127.0.0.1:4173'
    ).split(',') if s.strip()]

def cookie_options():
    return {'httponly': True, 'secure': os.getenv('LANDGUARD_ENV', 'development') == 'production',
            'samesite': 'Lax', 'path': '/api'}

def csrf_signer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='landguard-v2-csrf')

def create_csrf(response):
    nonce = secrets.token_urlsafe(32)
    token = csrf_signer().dumps({'nonce': nonce})
    response.set_cookie(COOKIE_CSRF, nonce, max_age=CSRF_MAX_AGE_SECONDS, **cookie_options())
    return token

def verify_csrf():
    # An attacker must obtain the JSON token and the matching HttpOnly cookie.
    origin = request.headers.get('Origin')
    if origin and origin.rstrip('/') not in allowed_origins():
        return False
    supplied = request.headers.get('X-CSRF-Token', '')
    cookie = request.cookies.get(COOKIE_CSRF, '')
    if not supplied or not cookie:
        return False
    try:
        parsed = csrf_signer().loads(supplied, max_age=CSRF_MAX_AGE_SECONDS)
        return hmac.compare_digest(str(parsed.get('nonce', '')), cookie)
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return False

def csrf_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        if not verify_csrf():
            return jsonify({'detail': 'Security check failed. Refresh and retry.'}), 403
        return function(*args, **kwargs)
    return decorated

def get_current_user():
    token = request.cookies.get(COOKIE_SESSION, '')
    if len(token) < 40:
        return None
    now = utcnow()
    with connect() as db:
        user = db.execute('''SELECT users.id, users.email, users.name, users.role
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.revoked_at IS NULL
            AND sessions.expires_at > ? AND users.is_active = 1''', (sha(token), now)).fetchone()
    return dict(user) if user else None

def login_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'detail': 'Login required'}), 401
        g.current_user = user
        return function(*args, **kwargs)
    return decorated

def role_required(*roles):
    def outer(function):
        @wraps(function)
        @login_required
        def decorated(*args, **kwargs):
            if g.current_user['role'] not in roles:
                return jsonify({'detail': 'Insufficient permissions'}), 403
            return function(*args, **kwargs)
        return decorated
    return outer

def login_user(response, user_id):
    token = secrets.token_urlsafe(48)
    expiration = (datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)).isoformat(timespec='seconds')
    with connect() as db:
        db.execute('INSERT INTO sessions(token_hash,user_id,created_at,expires_at) VALUES (?,?,?,?)',
                   (sha(token), user_id, utcnow(), expiration))
    response.set_cookie(COOKIE_SESSION, token, max_age=SESSION_HOURS*3600, **cookie_options())
    return response

def logout_user(response):
    token = request.cookies.get(COOKIE_SESSION, '')
    if token:
        with connect() as db:
            db.execute('UPDATE sessions SET revoked_at=? WHERE token_hash=?', (utcnow(), sha(token)))
    response.delete_cookie(COOKIE_SESSION, path='/api')
    return response

def authenticate(email, password):
    with connect() as db:
        row = db.execute('SELECT * FROM users WHERE email=? AND is_active=1', (email,)).fetchone()
    if row:
        try:
            if ph.verify(row['password_hash'], password):
                return dict(row)
        except (argon_errors.VerifyMismatchError, argon_errors.VerificationError, argon_errors.InvalidHashError):
            pass
    return None

def _principal_hash(value):
    return hmac.new(current_app.secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()

def rate_limit_key(email):
    return _principal_hash(email), _principal_hash(request.remote_addr or 'unknown')

def login_retry_after(email):
    """Account throttling + a larger independent IP cap.

    Five bad attempts against one account should not block every other
    account at the same home/school/office IP. The 30/IP ceiling still
    slows password spraying; both restrictions expire without manual SQL.
    """
    principal, ip = rate_limit_key(email)
    now = datetime.now(timezone.utc)
    since = (now - timedelta(minutes=15)).isoformat(timespec='seconds')
    with connect() as db:
        matching = db.execute(
            'SELECT principal_hash, ip_hash, created_at FROM login_attempts '
            'WHERE (principal_hash=? OR ip_hash=?) AND created_at>=? ORDER BY created_at DESC',
            (principal, ip, since)).fetchall()
    account_attempts = [row for row in matching if row['principal_hash'] == principal]
    ip_attempts = [row for row in matching if row['ip_hash'] == ip]
    oldest = None
    if len(account_attempts) >= 5:
        oldest = account_attempts[-5]['created_at']
    if len(ip_attempts) >= 30:
        candidate = ip_attempts[-30]['created_at']
        oldest = max(oldest, candidate) if oldest else candidate
    if not oldest:
        return 0
    try:
        # Database returns ISO-8601 UTC; ordered by timestamp descending below
        remaining = int((datetime.fromisoformat(oldest) + timedelta(minutes=15) - now).total_seconds()) + 1
    except (TypeError, ValueError):
        remaining = 900
    return max(1, min(900, remaining))


def rate_limited(email):
    return login_retry_after(email) > 0

def record_login_failure(email):
    principal, ip = rate_limit_key(email)
    with connect() as db:
        db.execute('INSERT INTO login_attempts(principal_hash,ip_hash,created_at) VALUES (?,?,?)',
                   (principal, ip, utcnow()))
        # Bound the table; no raw e-mail or IP is ever stored.
        cutoff = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat(timespec='seconds')
        db.execute('DELETE FROM login_attempts WHERE created_at<?', (cutoff,))

def clear_login_failures(email):
    principal, ip = rate_limit_key(email)
    with connect() as db:
        db.execute('DELETE FROM login_attempts WHERE principal_hash=? AND ip_hash=?', (principal, ip))

def audit_action(actor_id, event_type, result):
    audit(actor_id, event_type, result, str(uuid.uuid4()))
