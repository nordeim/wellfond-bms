lsof -i :8000 2>/dev/null || echo "Port 8000 is free"

cd /home/project/wellfond-bms && test -f .env && echo "✅ .env exists" || echo "❌ .env missing"

cd /home/project/wellfond-bms/backend && python manage.py showmigrations 2>&1 | tail -20

# Check core app migrations from backend directory
cd /home/project/wellfond-bms/backend && python manage.py showmigrations core 2>&1

# Check if admin user exists
cd /home/project/wellfond-bms/backend && python manage.py shell -c "from apps.core.models import User; print(f'Users: {User.objects.count()}'); u = User.objects.filter(username='admin').first(); print(f'Admin: {u}')" 2>&1

# Create test superuser in /home/project/wellfond-bms/backend
$ python manage.py shell -c "
from apps.core.models import User
from django.contrib.auth import get_user_model
User = get_user_model()
# Create superuser if not exists
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@wellfond.sg',
        password='Wellfond@2024!',
        first_name='Admin',
        last_name='User',
        role='management'
    )
    print(f'✅ Created superuser: {user.username}')
else:
    print('✅ Admin user already exists')
" 2>&1
20 objects imported automatically (use -v 2 for details).
✅ Created superuser: admin

cd /home/project/wellfond-bms/backend && rm -f /home/project/wellfond-bms/backend/nohup.out /home/project/wellfond-bms/backend/django.pid 2>/dev/null; nohup python manage.py runserver 0.0.0.0:8000 > nohup.out 2>&1 & echo $! > django.pid && echo "✅ Django started with PID: $(cat django.pid)"

kill $(cat /home/project/wellfond-bms/backend/django.pid) 2>/dev/null; sleep 1 && nohup python manage.py runserver 0.0.0.0:8000 > nohup.out 2>&1 & echo $! > django.pid && sleep 3 && echo "✅ Django restarted with PID: $(cat django.pid)"

# Test CSRF endpoint
curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf/ | python3 -m json.tool 2>/dev/null || echo "Raw response:"

# Test health check endpoint
$ curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null
{
    "status": "ok",
    "service": "wellfond-api",
    "version": "1.0.0"
}
Thinking: The CSRF endpoint didn't return a JSON response, but the health check works. Let me check the actual response and also verify the CSRF endpoint more carefully. Let me also check the nohup.out
# Test CSRF endpoint with status code
$ curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt -w "\n---HTTP %{http_code}---\n" http://localhost:8000/api/v1/auth/csrf/ 2>&1
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Page not found at /api/v1/auth/csrf/</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style>
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
…
Click to expand
# Get raw CSRF response
$ curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf/ 2>&1
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Page not found at /api/v1/auth/csrf/</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style>
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
…

kill $(cat django.pid) 2>/dev/null; sleep 1 && nohup python manage.py runserver 0.0.0.0:8000 > nohup.out 2>&1 & echo $! > django.pid && sleep 3 && echo "✅ Django restarted with PID: $(cat django.pid)"

# Clear Python bytecache
$ find /home/project/wellfond-bms/backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find /home/project/wellfond-bms/backend -type f -name "*.pyc" -delete 2>/dev/null; echo "✅ Bytecache cleared"

# Initialize cookie jar
$ rm -f /tmp/wellfond_cookies.txt && touch /tmp/wellfond_cookies.txt && chmod 600 /tmp/wellfond_cookies.txt
Thinking: Django server restarted. Now let me test the API
# Test CSRF endpoint
$ echo "1. Testing GET /api/v1/auth/csrf/" && curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt -w "\nHTTP %{http_code}\n" http://localhost:8000/api/v1/auth/csrf/ 2>&1 | python3 -m json.tool 2>/dev/null || echo "Raw response received"


# Get raw CSRF response
$ curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf/ 2>&1
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Page not found at /api/v1/auth/csrf/</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style>
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
…

# Test CSRF endpoint without trailing slash
$ echo "Testing without trailing slash..." && curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf 2>&1 | python3 -m json.tool 2>/dev/null || echo "Raw:" && curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf 2>&1 | head -20
Testing without trailing slash...
{
    "csrf_token": "Zc16fm7Vm6U6SPgi2vx3uPSppqiPjnWZ97uP7yc0beZFHyjPY367gf00a1XXcXOh"
}
{"csrf_token": "okDeMOl1wPKPUPGLbMyQm3XoGKBmVOE6yf6XE0q6lXPoJyJi7k7U8t5ZrlguOowo"}
Thinking: The CSRF endpoint is working now! The routers are registered. The issue was that Django Ninja doesn't use trailing slashes by default. The endpoint /api/v1/auth/csrf works.
Now let me
Excellent! CSRF endpoint working! Now continuing with the full
# Complete API endpoint testing suite
$ echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   Wellfond BMS API Endpoint Testing"
echo "═══════════════════════════════════════════════════════════════"
echo ""
# Test 1: Health Check
echo "1. GET /health/"
curl -s http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null
echo ""
# Test 2: Ready Check
echo "2. GET /ready/"
curl -s http://localhost:8000/ready/ | python3 -m json.tool 2>/dev/null
echo ""
# Test 3: CSRF Token
echo "3. GET /api/v1/auth/csrf"
CSRF_RESPONSE=$(curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf)
echo "$CSRF_RESPONSE" | python3 -m json.tool 2>/dev/null
CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
echo "   → CSRF Token extracted: ${CSRF_TOKEN:0:20}..."
echo ""
# Test 4: Login
echo "4. POST /api/v1/auth/login"
LOGIN_RESPONSE=$(curl -s -X POST -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -d '{"username":"admin","password":"Wellfond@2024!"}' \
  http://localhost:8000/api/v1/auth/login)
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""
# Test 5: Get Me (requires auth)
echo "5. GET /api/v1/auth/me"
curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  http://localhost:8000/api/v1/auth/me | python3 -m json.tool 2>/dev/null
echo ""
# Test 6: List Users (requires admin)
echo "6. GET /api/v1/users"
curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  http://localhost:8000/api/v1/users | python3 -m json.tool 2>/dev/null
echo ""
# Test 7: OpenAPI Schema
echo "7. GET /api/v1/openapi.json (available paths)"
curl -s http://localhost:8000/api/v1/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('   Available paths:'); [print(f'   - {p}') for p in sorted(d.get('paths',{}).keys())]" 2>/dev/null
echo ""
# Test 8: Logout
echo "8. POST /api/v1/auth/logout"
curl -s -X POST -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  http://localhost:8000/api/v1/auth/logout | python3 -m json.tool 2>/dev/null
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   API Testing Complete"
echo "═══════════════════════════════════════════════════════════════"
═══════════════════════════════════════════════════════════════
   Wellfond BMS API Endpoint Testing
═══════════════════════════════════════════════════════════════
1. GET /health/
{
    "status": "ok",
    "service": "wellfond-api",
    "version": "1.0.0"
}
…
Click to expand
Thinking: Login failed with "Invalid credentials". The password might be wrong or there might be an issue with the login function. Let me check the login function in auth.py to understand how it works and verify
Login failed. Let me debug
→ Read backend/apps/core/auth.py 

Now I need to restart the Django server for the changes
# Test all API endpoints after fixes
$ echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   Wellfond BMS API Endpoint Testing - Round 2"
echo "═══════════════════════════════════════════════════════════════"
echo ""
# Test 1: Health Check
echo "1. GET /health/"
curl -s http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null
echo ""
# Test 2: CSRF Token
echo "2. GET /api/v1/auth/csrf"
CSRF_RESPONSE=$(curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt http://localhost:8000/api/v1/auth/csrf)
echo "$CSRF_RESPONSE" | python3 -m json.tool 2>/dev/null
CSRF_TOKEN=$(echo "$CSRF_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['csrf_token'])" 2>/dev/null)
echo "   → CSRF Token: ${CSRF_TOKEN:0:20}..."
echo ""
# Test 3: Login (using email instead of username)
echo "3. POST /api/v1/auth/login (with email)"
LOGIN_RESPONSE=$(curl -s -X POST -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -d '{"email":"admin@wellfond.sg","password":"Wellfond@2024!"}' \
  http://localhost:8000/api/v1/auth/login)
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "Response: $LOGIN_RESPONSE"
echo ""
# Test 4: Get Me (requires auth)
echo "4. GET /api/v1/auth/me"
ME_RESPONSE=$(curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  http://localhost:8000/api/v1/auth/me)
echo "$ME_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "Response: $ME_RESPONSE"
echo ""
# Test 5: List Users (requires admin)
echo "5. GET /api/v1/users"
USERS_RESPONSE=$(curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  http://localhost:8000/api/v1/users)
echo "$USERS_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))" 2>/dev/null || echo "Response: $USERS_RESPONSE"
echo ""
# Test 6: Logout
echo "6. POST /api/v1/auth/logout"
LOGOUT_RESPONSE=$(curl -s -X POST -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  http://localhost:8000/api/v1/auth/logout)
echo "$LOGOUT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "Response: $LOGOUT_RESPONSE"
echo ""
# Test 7: Verify logout (me should fail)
echo "7. GET /api/v1/auth/me (after logout - should fail)"
ME_AFTER_LOGOUT=$(curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  http://localhost:8000/api/v1/auth/me)
echo "$ME_AFTER_LOGOUT" | python3 -m json.tool 2>/dev/null || echo "Response: $ME_AFTER_LOGOUT"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   API Testing Complete"
echo "═══════════════════════════════════════════════════════════════"
═══════════════════════════════════════════════════════════════
   Wellfond BMS API Endpoint Testing - Round 2
═══════════════════════════════════════════════════════════════
1. GET /health/
{
    "status": "ok",
    "service": "wellfond-api",
    "version": "1.0.0"
}
…
Click to expand
Thinking: Still getting an internal server error on login. Let me
# Check Django error logs
$ tail -100 /home/project/wellfond-bms/backend/nohup.out 2>&1 | grep -A 20 "Internal Server Error"

# Rerun tests after fix
$ DJANGO_SETTINGS_MODULE=config.settings.development PYTHONPATH=/home/project/wellfond-bms/backend:$PYTHONPATH python -m pytest tests/test_logs.py -v --tb=short 2>&1 | head -80
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/venv/bin/python
cachedir: .pytest_cache
django: version: 6.0.4, settings: config.settings.development (from env)
PySide6 6.9.2 -- Qt runtime 6.9.2 -- Qt compiled 6.9.2
hypothesis profile 'default'
rootdir: /home/project/wellfond-bms
plugins: asyncio-1.3.0, django-4.12.0, respx-0.22.0, qt-4.5.0, Faker-40.5.1, mock-3.12.0, langsmith-0.5.1, logfire-4.16.0, anyio-4.13.0, cov-7.1.0, xdist-3.8.0, hypothesis-6.151.11
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 11 items
…

# Run tests after fixes
$ DJANGO_SETTINGS_MODULE=config.settings.development PYTHONPATH=/home/project/wellfond-bms/backend:$PYTHONPATH python -m pytest tests/test_logs.py -v --tb=short 2>&1

# Create migrations for breeding app in /home/project/wellfond-bms/backend
$ python manage.py makemigrations breeding 2>&1

# Apply breeding migrations in /home/project/wellfond-bms/backend
$ python manage.py migrate breeding 2>&1

# Verify API loads with Django settings in /home/project/wellfond-bms/backend
$ DJANGO_SETTINGS_MODULE=config.settings.development python -c "from api import api; print('API loaded successfully'); print(f'Total routes: {len(api.urls)}')" 2>&1

# Run test_auth.py to verify fixes
$ cd /home/project/wellfond-bms/backend && DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest apps/core/tests/test_auth.py -v --tb=short 2>&1

# Run test_permissions.py to verify fixes
$ DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest apps/core/tests/test_permissions.py -v --tb=short 2>&1 | head -80

# Run test_permissions.py from project root
$ cd /home/project/wellfond-bms && DJANGO_SETTINGS_MODULE=backend.config.settings.development python -m pytest backend/apps/core/tests/test_permissions.py -v --tb=short 2>&1

# Run sales tests from backend directory
$ cd /home/project/wellfond-bms/backend && python -m pytest apps/sales/tests/ -v --tb=short 2>&1 | tee /tmp/test_output.txt | tail -150

