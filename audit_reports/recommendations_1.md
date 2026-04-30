1. Immediate (before any production deployment):
   - Remove .env from git tracking (git rm --cached .env)
   - Fix SessionManager to use caches["sessions"] instead of cache
   - Add SECRET_KEY fail-fast in production settings
   - Add PgBouncer and Gotenberg services to compose
   - Bind Redis to 127.0.0.1 only
   - Remove PostgreSQL trust auth method
2. Before Staging:
   - Upgrade sslmode to "require" in production
   - Add django-csp to requirements (or remove CSP settings as dead code)
   - Fix pythonjson-logger formatter class path
   - Unify Celery beat schedule (remove from base.py, keep in celery.py)
   - Change celery.py default to development settings
   - Add automatic session refresh in AuthenticationMiddleware
   - Add logging to generic exception handler in API
3. Before Production Go-Live:
   - Add production Docker Compose with PgBouncer, Gotenberg, multiple Redis instances, Celery worker/beat
   - Switch psycopg2-binary to psycopg2 in production requirements
   - Remove JWT libraries from production deps (or document their purpose)
   - Remove NLTK from base requirements
   - Fix pytest-asyncio version
   - Add gunicorn + uvicorn to requirements
   - Resolve cookie name conflict (custom auth vs Django SessionMiddleware)
   - Add production ALLOWED_HOSTS validation
