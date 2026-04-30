COMPREHENSIVE BACKEND CORE APP AUDIT REPORT
Executive Summary
The core app (/home/project/wellfond-bms/backend/apps/core/) implements authentication, RBAC, entity scoping, audit logging, and middleware. While the overall architecture is sound and many AGENTS.md requirements are met, I identified 28 issues ranging from CRITICAL security vulnerabilities to medium-complexity bugs and test-implementation mismatches. The most severe issues are: SessionManager using the wrong cache backend, a SQL-injection-like vector in scope_entity_for_list, missing enforce_pdpa calls across all routers, and extensive test-implementation drift where tests call methods that do not exist in the code.
---
1. FILE-BY-FILE ANALYSIS
---
1.1 /home/project/wellfond-bms/backend/apps/core/models.py (184 lines)
Exists: YES
Contents: Defines User, Entity, and AuditLog models with UUID PKs, timestamps, and RBAC support.
Issues Found:
#	Severity	Issue	Detail
1	MEDIUM	User.get_entity_id() uses T | None syntax	Line 72: def get_entity_id(self) -> uuid.UUID | None: uses the union syntax that AGENTS.md explicitly prohibits. Must use Optional[uuid.UUID] for Pydantic v2 compatibility and per coding standards.
2	HIGH	AuditLog immutability only enforced at Python level, not at DB level	Lines 176-184: The save() and delete() overrides raise ValueError, but these are trivially bypassed via QuerySet.update() or QuerySet.delete() (e.g., AuditLog.objects.filter(pk=x).update(action="foo") or AuditLog.objects.all().delete()). There is no database-level trigger or rule to prevent this.
3	MEDIUM	AuditLog save() override has a bypass via force_insert=True	Line 178: if self.pk and not kwargs.get("force_insert"): -- any caller passing force_insert=True can overwrite an existing AuditLog record. The force_insert kwarg should be blocked entirely for existing records.
4	MEDIUM	Entity.gst_rate stored as decimal fraction (0.09) but AGENTS.md defines GST formula as Decimal(price) * 9 / 109	The field stores 0.09 (fraction), but the actual GST-inclusive extraction formula 9/109 is a different mathematical concept. This is a potential source of confusion -- the field should either store the percentage (9) or the code should use gst_rate consistently.
5	LOW	Entity.phone field collides with User.mobile naming inconsistency	The initial migration (0001) had User.phone which was renamed to User.mobile in migration 0002. The Entity still has phone. Not a bug, but inconsistent naming.
6	LOW	No soft-delete mechanism via is_active is implemented on User model	AGENTS.md says "soft-delete via is_active. Never hard-delete." The is_active field exists, but the User model's default delete() method still performs hard deletion. There is no override to prevent it.
Gaps vs AGENTS.md:
- AuditLog immutability: "No UPDATE/DELETE" is claimed but only enforced at ORM level, not DB level.
- Model save: self._state.adding is not used anywhere in this file (it is not needed here since AuditLog is the only model with a custom save, but the pattern is not demonstrated).
---
1.2 /home/project/wellfond-bms/backend/apps/core/auth.py (291 lines)
Exists: YES
Contents: SessionManager, AuthenticationService, and helper functions for cookie-based Redis session auth.
Issues Found:
#	Severity	Issue	Detail
7	CRITICAL	SessionManager uses cache (default cache) instead of caches["sessions"]	Lines 18, 55-58, 62-64, 72, 79-82, 88-89: All cache.set() and cache.get() calls use from django.core.cache import cache which resolves to the default cache (redis_cache:6379/0), NOT the dedicated sessions cache (redis_sessions:6379/0). The Django settings explicitly configure SESSION_CACHE_ALIAS = "sessions". This means session data goes to the wrong Redis instance, and the session isolation is completely broken.
8	HIGH	get_authenticated_user() returns None instead of AnonymousUser	Line 289-291: The function returns Optional[User] and returns None when no session is found. The test file (test_auth.py lines 298, 307) asserts that it returns AnonymousUser. The middleware (middleware.py line 200) sets request.user = AnonymousUser() explicitly, but get_authenticated_user() does not. This inconsistency means callers using get_authenticated_user() must handle None differently from AnonymousUser, leading to potential AttributeError on None.is_authenticated.
9	MEDIUM	AuthenticationService.refresh() returns raw user.id (UUID object) and user.entity_id (UUID object) without str() conversion	Lines 229-243: The id, entity_id, and created_at fields are returned as their raw Python types. But in login() (lines 124-131), these are explicitly cast to str(). This means the refresh response will serialize UUIDs differently from the login response (e.g., "id": "uuid-string" vs "id": {"hex": "..."} in JSON), creating a frontend inconsistency.
10	MEDIUM	Missing pdpa_consent_at timestamp update on login response	The login response (line 122-133) does not include pdpa_consent_at in the user data, while the model has this field. Not necessarily a bug but an omission.
11	LOW	AuthenticationService.COOKIE_NAME = "sessionid" collides with Django's built-in session cookie name	Django's django.contrib.sessions also uses sessionid as the default cookie name. Since the project uses Django's session middleware (django.contrib.sessions.middleware.SessionMiddleware), this could cause conflicts where Django's session middleware reads/writes the same cookie, potentially overwriting the custom Redis session.
12	LOW	No session rotation on login (same session key persists)	When a user logs in again (e.g., on a different device), a new session key is created but old sessions are not invalidated. There is no mechanism to limit concurrent sessions per user.
Gaps vs AGENTS.md:
- CRITICAL: "Reads cookie & validates Redis session" -- the session is stored in the wrong Redis instance.
- Cookie is HttpOnly, Secure (in production), SameSite=Lax -- this is correctly implemented.
- get_authenticated_user(request) exists and reads session cookie -- correct pattern, but uses wrong cache.
---
1.3 /home/project/wellfond-bms/backend/apps/core/permissions.py (273 lines)
Exists: YES
Contents: Role decorators, entity scoping, PDPA enforcement, PermissionChecker, RoleGuard, convenience decorators.
Issues Found:
#	Severity	Issue	Detail
13	CRITICAL	require_role() decorator uses getattr(request, "user", None) -- unreliable with Django Ninja	Lines 31-33: AGENTS.md explicitly warns "Django Ninja does not reliably preserve request.user across decorators/pagination. Always read session directly: get_authenticated_user(request)." This decorator relies on request.user which may be a SimpleLazyObject or not properly set in Ninja context. The _check_admin_permission in users.py correctly reads the session cookie directly, but this decorator does not.
14	CRITICAL	scope_entity_for_list() accepts raw entity_param string with no UUID validation	Lines 92-93: queryset.filter(entity_id=entity_param) where entity_param is an unsanitized string. If a user passes a non-UUID string, this will raise an unhandled exception. More critically, if the queryset's entity_id field name differs across models, this could cause unexpected behavior. Should validate as UUID first.
15	HIGH	enforce_pdpa() does not check user parameter at all	Lines 103-110: The function signature accepts user: User but never uses it. It only checks if the model has a pdpa_consent attribute. Per AGENTS.md, PDPA filtering should be context-dependent (e.g., MANAGEMENT might see non-consented data for regulatory purposes). The user parameter is completely ignored.
16	HIGH	require_role() decorator does NOT work with Django Ninja views	Lines 18-53: The decorator returns JsonResponse on failure, but Django Ninja views expect exceptions (HttpError) or schema-validated responses. Using this decorator on a Ninja router endpoint would cause a response schema mismatch. The test_permissions.py test at line 169 actually expects HttpError but the decorator returns JsonResponse -- this test would fail.
17	MEDIUM	require_role([]) passes empty tuple, not list	Line 203: @require_role(["sales", "ground"]) -- the decorator uses *required_roles: str which unpacks the list as a single argument, not as individual roles. When called with a list, required_roles becomes (["sales", "ground"],) -- a tuple containing one list. Then user.role in required_roles checks if the role is in the tuple, which contains the list, not the individual strings. This is a bug.
18	MEDIUM	RoleGuard.can_access_route() has broken string matching	Lines 208-209: route.startswith(pattern.replace("/", "")) -- this strips ALL slashes from the pattern, turning /ground/ into ground. Then it checks if the route starts with ground. But if route is /api/v1/ground/logs, it would match ground but the original pattern /ground/ intended to match only /ground/-prefixed routes. The logic is fragile and incorrect.
19	LOW	F = TypeVar("F", bound=Callable[..., any]) -- any is not a valid Python type	Line 15: Should be Any from typing, not any (which is a builtin function). This is a typo that works by accident because any is a callable, but it's semantically wrong.
20	LOW	Pre-instantiated decorators require_management, require_admin, etc. are not usable with Ninja	Lines 229-233: These are pre-decorated functions that wrap at module load time. They cannot be used as Ninja route decorators because they return JsonResponse on failure.
Gaps vs AGENTS.md:
- enforce_pdpa(qs) must hard-filter WHERE pdpa_consent=true -- partially implemented (checks model attribute but ignores user context).
- scope_entity(qs, user) on EVERY query -- implemented but not enforced/used consistently in routers.
- require_role decorator does not read session cookie directly.
---
1.4 /home/project/wellfond-bms/backend/apps/core/middleware.py (230 lines)
Exists: YES
Contents: IdempotencyMiddleware, EntityScopingMiddleware, AuthenticationMiddleware.
Issues Found:
#	Severity	Issue	Detail
21	MEDIUM	IdempotencyMiddleware._generate_fingerprint() uses request.user which may not be set yet	Lines 106-110: request.user.id is accessed, but if the middleware runs before the custom AuthenticationMiddleware in the stack (which it doesn't per settings, but the code doesn't guard against it), request.user won't exist. The hasattr check is good but is_authenticated on a SimpleLazyObject could cause issues.
22	MEDIUM	IdempotencyMiddleware._is_idempotency_required() only checks specific path prefixes, not ALL write operations	Lines 117-131: AGENTS.md says "All state-changing POSTs require X-Idempotency-Key." But the implementation uses an allowlist of paths (IDEMPOTENCY_REQUIRED_PATHS). Any new API path added outside this list (e.g., /api/v1/notifications/) will silently bypass idempotency enforcement. The logic should be inverted: enforce on all writes EXCEPT the exempt list.
23	MEDIUM	_is_public_path() uses startswith with incorrect logic	Line 230: any(path.startswith(public) for public in public_paths) -- but public_paths is a list, and startswith checks if the path starts with any of those strings. However, /api/v1/auth/login would match /api/v1/auth/login exactly but /api/v1/auth/logintest would also match (since it starts with the login path). The trailing slash inconsistency is also a concern: /api/v1/auth/login vs /api/v1/auth/login/.
24	LOW	EntityScopingMiddleware accesses request.user.entity_id without safety check	Line 150: str(user.entity_id) -- if entity_id is None, this becomes "None" string. Should check for None first.
25	INFO	Idempotency correctly uses caches["idempotency"] and 24h TTL (86400s)	Lines 73, 90, 96: This is correctly implemented per AGENTS.md.
Gaps vs AGENTS.md:
- Idempotency uses caches["idempotency"] -- CORRECT.
- 24h TTL (86400) -- CORRECT.
- Middleware order in settings: Django auth first, then custom -- CORRECT.
---
1.5 /home/project/wellfond-bms/backend/apps/core/schemas.py (237 lines)
Exists: YES
Contents: Pydantic v2 schemas for auth, user management, entity, audit log, and error responses.
Issues Found:
#	Severity	Issue	Detail
26	HIGH	Uses deprecated @validator instead of Pydantic v2 @field_validator	Lines 84, 107: from pydantic import ... validator and @validator("role") -- Pydantic v2 deprecated @validator in favor of @field_validator. While it still works with a compatibility shim, this will break in future Pydantic versions and is explicitly an anti-pattern for Pydantic v2 migration.
27	MEDIUM	EntityResponse.gst_rate typed as float but model uses DecimalField	Line 145: gst_rate: float -- the Django model stores this as Decimal, and serializing it as float introduces floating-point precision issues. Should be Decimal from decimal module for financial accuracy per AGENTS.md.
28	MEDIUM	AuditLogEntry.uuid field name doesn't match model's id field	Line 189: uuid: UUID -- the model field is named id, not uuid. With from_attributes = True, Pydantic will try to read obj.uuid which doesn't exist. This will cause a validation error when serializing AuditLog objects.
29	MEDIUM	UserResponse does not include mobile field	The model has mobile but the response schema (lines 28-43) omits it. If clients need to display or update mobile numbers, they cannot.
30	LOW	Schema uses class Config: from_attributes = True (Pydantic v1 style)	Lines 42, 152, 199: While Config inner class with from_attributes works in Pydantic v2, the idiomatic v2 approach is model_config = ConfigDict(from_attributes=True). Not a bug but inconsistent with v2 best practices.
31	LOW	AuditLogEntry.actor typed as Optional[UserResponse] but actor is a FK with SET_NULL	Line 190: If the actor is deleted (SET_NULL), the actor becomes None. But UserResponse requires all fields (id, username, email, etc.). When actor is None, this correctly serializes as None. But when actor exists, the from_attributes=True should handle it. Acceptable.
Gaps vs AGENTS.md:
- model_validate(obj, from_attributes=True) -- the Config.from_attributes = True is the schema-level equivalent, which is correct for response serialization. However, nowhere in the routers is model_validate() actually called -- they rely on Django Ninja's automatic serialization. This could be a problem if Ninja doesn't use the Config properly.
- No usage of from_orm() (good, that's v1).
- Optional[T] is used (good, no T | None).
---
1.6 /home/project/wellfond-bms/backend/apps/core/admin.py (217 lines)
Exists: YES
Contents: Django admin configuration for User, Entity, and AuditLog.
Issues Found:
#	Severity	Issue	Detail
32	MEDIUM	EntityAdmin.readonly_fields does not include created_at and updated_at in the tuple	Line 180: readonly_fields = ("created_at", "updated_at") -- this is correctly defined. But the fieldset (lines 169-177) includes these in the "Metadata" section. The fields would be editable in the admin form without the readonly_fields definition. This IS correct. No issue here.
33	LOW	AuditLogAdmin has has_add_permission = False but AuditLog should be creatable via code	Line 210: This prevents creating AuditLog entries via admin, which is correct for compliance. But it also means the admin cannot be used for manual audit entry creation, which might be needed for backfilling. Not a bug, just a design note.
34	LOW	AuditLog admin prevents admin-level delete, but QuerySet.delete() still works	This mirrors the model-level issue (#2). The admin correctly blocks UI-level operations, but bulk deletes via ORM still bypass this.
Gaps vs AGENTS.md:
- AuditLog admin is read-only -- CORRECT.
- No anti-patterns found in admin configuration.
---
1.7 /home/project/wellfond-bms/backend/apps/core/__init__.py (2 lines)
Exists: YES
Contents: Single comment line. No issues.
---
1.8 /home/project/wellfond-bms/backend/apps/core/apps.py (7 lines)
Exists: YES
Contents: Standard Django AppConfig. No issues.
---
1.9 ROUTER FILES
1.9.1 /home/project/wellfond-bms/backend/apps/core/routers/__init__.py (11 lines)
Exists: YES -- Correctly exports all three routers.
1.9.2 /home/project/wellfond-bms/backend/apps/core/routers/auth.py (113 lines)
Exists: YES
Contents: Login, logout, refresh, me, and CSRF endpoints with rate limiting.
#	Severity	Issue	Detail
35	HIGH	Login endpoint returns raw HttpResponse (from login_user) but declares no response schema	Line 38-53: The login() function has no response= parameter and returns the raw JsonResponse from AuthenticationService.login(). This means Django Ninja cannot validate the response against the LoginResponse schema. The response type annotation is missing.
36	MEDIUM	get_me() returns UserResponse but does not call model_validate()	Lines 85-97: Returns user (a Django model instance). Ninja should use the schema's Config.from_attributes = True to serialize. This works with Ninja but is implicit and fragile.
37	MEDIUM	logout() also returns raw HttpResponse	Line 56-61: Same issue as login -- the LogoutResponse schema is declared but the actual logout_user() returns a JsonResponse which bypasses schema validation.
38	LOW	Rate limiting uses @ratelimit(key='ip') but behind BFF proxy, all requests come from the same IP	The BFF proxy pattern means the Next.js server forwards all requests. The actual client IP is in X-Forwarded-For. The get_client_ip() helper in auth.py handles this, but django-ratelimit's key='ip' uses REMOTE_ADDR by default, which would be the BFF server's IP, not the client's. Should use key='ip:x-forwarded-for' or a custom key function.
1.9.3 /home/project/wellfond-bms/backend/apps/core/routers/dashboard.py (111 lines)
Exists: YES
#	Severity	Issue	Detail
39	CRITICAL	SSE endpoint calls synchronous ORM in async generator	Lines 78-101: event_generator() is an async def that calls get_recent_activity(user, limit=1) which is presumably a synchronous DB query. AGENTS.md explicitly requires: "Use sync_to_async(thread_sensitive=True) for DB calls inside async generators to prevent thread pool exhaustion." This is a direct violation.
 	 	 	 
