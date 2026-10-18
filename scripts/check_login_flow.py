r"""Local-only live smoke test for Vite -> Flask -> PostgreSQL login.

Run from project root after BOTH dev servers are running:
    .\backend\.venv\Scripts\python.exe scripts\check_login_flow.py --email admin@example.test

Password is read via getpass and never printed, put on the command line,
or written to disk. Checks session creation and revocation without touching land records.
"""
import argparse
import getpass
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin


def request(opener, base, path, *, method='GET', token='', payload=None):
    headers = {'Accept':'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token:
        headers['X-CSRF-Token'] = token
    if method != 'GET':
        headers['Origin'] = base.rstrip('/')
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(urljoin(base.rstrip('/')+'/', path.lstrip('/')),
                                 method=method, data=data, headers=headers)
    try:
        with opener.open(req, timeout=12) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as exc:
        try:
            exc.read()
        except Exception:
            pass
        return exc.code, {}


def main():
    parser = argparse.ArgumentParser(description='Safely test local Login + Session + Logout; no passwords printed.')
    parser.add_argument('--email', required=True)
    parser.add_argument('--base', default='http://localhost:4173', help='Vite dev URL; default http://localhost:4173')
    opts = parser.parse_args()
    if not opts.base.startswith(('http://localhost:', 'http://127.0.0.1:')):
        parser.error('For safety, only a local development server is supported.')
    base = opts.base.rstrip('/')
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        status, health = request(opener, base, '/api/health')
        if status != 200 or health.get('status') != 'ok':
            print('FAIL: API health is not ready. Start Docker, Flask, and Vite; verify proxy configuration.')
            return 1
        print('OK: Frontend /api proxy reaches Flask')
        print('Database backend:', health.get('database_backend', 'unknown'))
        if health.get('database_backend') != 'postgresql':
            print('WARNING: API is not connected to PostgreSQL. Check backend/.env locally.')
        status, csrf = request(opener, base, '/api/auth/csrf')
        token = csrf.get('csrf_token') if isinstance(csrf, dict) else None
        if status != 200 or not token:
            print('FAIL: CSRF challenge unavailable (HTTP status {}).'.format(status))
            return 1
        print('OK: Session/CSRF challenge available')
        password = getpass.getpass('Existing account password (hidden): ')
        if not password:
            print('Stopped: Empty password. No login attempt performed.')
            return 1
        status, result = request(opener, base, '/api/auth/login', method='POST', token=token,
                                 payload={'email':opts.email,'password':password})
        del password
        if status != 200:
            print('FAIL: Login returned HTTP {}.'.format(status))
            if status == 401: print('Check existing account email and password; use CLI reset-password if required.')
            elif status == 429: print('Temporary login rate limit. Wait before retrying; do not brute-force.')
            elif status == 403: print('CSRF/Origin problem. Access the site consistently via localhost:4173.')
            elif status >= 500: print('Inspect the Flask terminal traceback; do not share secrets.')
            else: print('Inspect the Flask terminal for a request validation error.')
            return 2
        print('OK: Login accepted (role: {})'.format(result.get('user_role','unknown')))
        status, session = request(opener, base, '/api/auth/me')
        if status != 200 or not session.get('user_id'):
            print('FAIL: Login accepted but cookie session not restored (HTTP {}).'.format(status))
            return 2
        print('OK: HttpOnly session restored through Vite proxy')
        status, csrf = request(opener, base, '/api/auth/csrf')
        status, _ = request(opener, base, '/api/auth/logout', method='POST',token=csrf.get('csrf_token',''))
        if status != 200:
            print('FAIL: Logout returned HTTP {}.'.format(status))
            return 2
        status, _ = request(opener, base, '/api/auth/me')
        if status != 401:
            print('FAIL: Session remains accessible after logout (HTTP {}).'.format(status))
            return 2
        print('PASS: Login, session, and logout smoke test completed.')
        return 0
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        print('FAIL: Local HTTP/proxy request failed ({}).'.format(type(exc).__name__))
        print('Start Docker and Flask first, then Vite; check localhost:4173/api/health.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
