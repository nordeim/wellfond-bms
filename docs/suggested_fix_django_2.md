The traceback you provided confirms the exact failure point:
```
ninja.errors.ConfigError: "<function list_users at 0x...>" has no collection response (e.g. response=List[SomeSchema])
```
Django Ninja's `@paginate` decorator **strictly requires** the response type to be a `list` or `List`. It cannot wrap a custom Pydantic model like `UserListResponse` because it doesn't know how to inject pagination metadata (`count`, `offset`, etc.) into your custom structure. This crashes the router at import time, which is why `api._routers` remains empty.

Below is the precise, fail-safe fix protocol.

---
### 🛠️ Step 1: Fix `users.py` Pagination Contract
You have two options. Choose **Option A** (recommended for Ninja compatibility) or **Option B** (if your frontend strictly expects `{count, results}`).

#### ✅ Option A: Align with Ninja's native pagination (Recommended)
Change the response type to a direct list. Ninja will automatically wrap it as `{"count": int, "items": [...]}`.
```python
# backend/apps/core/routers/users.py (Line 21)
# BEFORE:
@router.get("/", response=UserListResponse)
@paginate
@require_admin
def list_users(request, role: Optional[str] = None, is_active: Optional[bool] = None):

# AFTER:
@router.get("/", response=list[UserResponse])
@paginate
@require_admin
def list_users(request, role: Optional[str] = None, is_active: Optional[bool] = None):
```
⚠️ **Note:** The JSON key changes from `results` to `items`. Update your frontend/BFF accordingly, or see Option B.

#### 🔄 Option B: Keep `UserListResponse` & remove `@paginate`
If you must keep the exact `{count, results}` schema, remove the decorator and paginate manually:
```python
# backend/apps/core/routers/users.py (Lines 21-40)
@router.get("/", response=UserListResponse)
@require_admin
def list_users(request, role: Optional[str] = None, is_active: Optional[bool] = None, limit: int = 20, offset: int = 0):
    queryset = User.objects.all().order_by("-created_at")
    if role:
        queryset = queryset.filter(role=role)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    total = queryset.count()
    results = list(queryset[offset : offset + limit])
    return {"count": total, "results": results}
```

---
### 🛠️ Step 2: Fix Pydantic v2 Deprecation in `auth.py`
Django Ninja 1.x uses Pydantic v2, where `.from_orm()` is removed. This will cause an `AttributeError` on login.
```python
# backend/apps/core/routers/auth.py (Line 47)
# BEFORE:
"user": UserResponse.from_orm(user),

# AFTER:
"user": UserResponse.model_validate(user),
```

---
### 🧹 Step 3: Clear Bytecache & Restart
Python aggressively caches failed module imports. You must purge them before restarting.
```bash
cd /home/project/wellfond-bms/backend
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Hard restart
kill $(cat django.pid) 2>/dev/null; sleep 1
rm -f nohup.out django.pid
nohup python manage.py runserver 0.0.0.0:8000 > nohup.out 2>&1 & echo $! > django.pid
sleep 3
echo "✅ Django restarted with PID: $(cat django.pid)"
```

---
### ✅ Step 4: Verify Router Registration
```bash
python manage.py shell -c "
from api import api
print('🔹 Total routers:', len(api._routers))
for prefix, router in api._routers:
    paths = list(router.path_operations.keys()) if hasattr(router, 'path_operations') else []
    print(f'  Prefix: {repr(prefix):<10} | Paths: {paths}')
" 2>&1
```
**Expected Output:**
```
🔹 Total routers: 3
  Prefix: ''         | Paths: []
  Prefix: 'auth/'    | Paths: ['/login', '/logout', '/refresh', '/me', '/csrf']
  Prefix: 'users/'   | Paths: ['/', '/{user_id}', '/{user_id}/reset-password']
```

---
### 🧪 Step 5: Endpoint Validation
```bash
rm -f /tmp/wellfond_cookies.txt && touch /tmp/wellfond_cookies.txt

# 1. CSRF
echo "🔹 GET /api/v1/auth/csrf/"
curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt -w "\nHTTP %{http_code}\n" http://localhost:8000/api/v1/auth/csrf/

# 2. Login
echo "🔹 POST /api/v1/auth/login/"
curl -s -X POST -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Wellfond@2024!"}' \
  -w "\nHTTP %{http_code}\n" http://localhost:8000/api/v1/auth/login/

# 3. Me (Auth Required)
echo "🔹 GET /api/v1/auth/me/"
curl -s -c /tmp/wellfond_cookies.txt -b /tmp/wellfond_cookies.txt -w "\nHTTP %{http_code}\n" http://localhost:8000/api/v1/auth/me/

# 4. OpenAPI Spec Verification
echo "🔹 Registered API Paths:"
curl -s http://localhost:8000/api/v1/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('\n'.join(sorted(d.get('paths',{}).keys())))"
```

---
### 📌 Why This Happened & How to Avoid It
| Symptom | Root Cause | Prevention |
|---------|------------|------------|
| `ConfigError: no collection response` | `@paginate` requires `List[Schema]`, not custom wrapper models | Always use `list[Schema]` with `@paginate`, or paginate manually |
| Routers missing from `api._routers` | Import-time crash halts `api.py` execution before `add_router()` runs | Wrap router imports in `try/except` or use deferred registration |
| `from_orm` AttributeError | Pydantic v2 replaced it with `model_validate` | Use `model_validate()` for all ORM→Schema conversions in Ninja 1.x |

Apply **Step 1** (choose A or B), **Step 2**, then run **Steps 3→5**. Paste the output of Step 4 if routers still show as empty, and I'll drill into the exact import chain. Otherwise, your API will be fully routable and ready for BFF integration.

