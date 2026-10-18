"""Interactive local provisioning; no hardcoded or public default credentials."""
import argparse
import getpass
import re
import uuid
from app.auth import ph
from app.database import connect, initialize, utcnow


def main():
    parser = argparse.ArgumentParser(description='Create local Smart LandGuard user (not an identity verification)')
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('--role', choices=['buyer','seller','admin'], required=True)
    create.add_argument('--email', required=True)
    create.add_argument('--name', required=True)
    reset = sub.add_parser('reset-password', help='Local operator recovery; private console only')
    reset.add_argument('--email', required=True)
    args = parser.parse_args()
    if args.command == 'create':
        email = args.email.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            parser.error('Valid email required')
        password = getpass.getpass('Choose a unique password (minimum 12 characters): ')
        if len(password) < 12 or len(password) > 128 or password.strip() == '':
            parser.error('Password must be 12–128 characters')
        if password != getpass.getpass('Confirm password: '):
            parser.error('Passwords do not match')
        initialize()
        with connect() as db:
            db.execute('INSERT INTO users(id,email,name,role,password_hash,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                       (str(uuid.uuid4()), email, args.name.strip()[:100], args.role, ph.hash(password), utcnow(), utcnow()))
        print(f'Created {args.role} account: {email}. Credentials are never printed or stored in plaintext.')
    elif args.command == 'reset-password':
        email = args.email.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            parser.error('Valid email required')
        initialize()
        with connect() as db:
            user = db.execute('SELECT id FROM users WHERE email=? AND is_active=1', (email,)).fetchone()
        if not user:
            parser.error('No active local account found for this email')
        new_password = getpass.getpass('New password (12–128 characters, not shown): ')
        if not 12 <= len(new_password) <= 128 or not new_password.strip():
            parser.error('Password must be 12–128 characters')
        if new_password != getpass.getpass('Confirm new password: '):
            parser.error('Passwords do not match')
        with connect() as db:
            db.execute('UPDATE users SET password_hash=?, updated_at=? WHERE id=?',
                       (ph.hash(new_password), utcnow(), user['id']))
            db.execute('UPDATE sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL',
                       (utcnow(), user['id']))
            # A verified local operator can clear this account's lockout safely,
            # but the wider IP throttling still protects other accounts.
            from hashlib import sha256
            import hmac
            import os
            secret = os.getenv('LANDGUARD_SECRET_KEY')
            if secret:
                principal = hmac.new(secret.encode(), email.encode(), sha256).hexdigest()
                db.execute('DELETE FROM login_attempts WHERE principal_hash=?', (principal,))
        print('Password reset and previous sessions revoked for local account. No credentials printed.')

if __name__ == '__main__':
    main()
