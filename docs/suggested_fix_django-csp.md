**Root‑Cause Analysis & Remediation Plan**

---

## 1. Error Decoded

```
django.core.management.base.SystemCheckError: SystemCheckError: System check identified some issues:

ERRORS:
?: (csp.E001) You are using django-csp < 4.0 settings. Please update your settings to use the new format.
See https://django-csp.readthedocs.io/en/latest/migration-guide.html for more information.
```

The error is raised by the **django‑csp 4.0 system check** (`csp.E001`). It fires because the settings files still contain the old‑style `CSP_*` prefixed variables, which are now unsupported.

---

## 2. Why It Happens in Your Project

| File | Old‑style settings still present |
|------|----------------------------------|
| `backend/config/settings/base.py` | `CSP_DEFAULT_SRC`, `CSP_SCRIPT_SRC`, `CSP_STYLE_SRC`, `CSP_IMG_SRC`, `CSP_CONNECT_SRC`, `CSP_FONT_SRC`, `CSP_REPORT_ONLY` |
| `backend/config/settings/development.py` | `CSP_SCRIPT_SRC` (overridden), `CSP_REPORT_ONLY` (overridden) |

Even though you also defined the new `CONTENT_SECURITY_POLICY` and `CONTENT_SECURITY_POLICY_REPORT_ONLY` dicts, the **mere presence** of the old `CSP_*` variables makes django‑csp 4.0 abort with `csp.E001`.

---

## 3. Research Summary

1. **django‑csp 4.0 Breaking Changes** – The configuration format was completely reworked. Individual `CSP_*` settings are **no longer recognised**; all configuration must be placed inside `CONTENT_SECURITY_POLICY` and/or `CONTENT_SECURITY_POLICY_REPORT_ONLY` dictionaries.

2. **CSP_REPORT_ONLY boolean** – The old boolean flag `CSP_REPORT_ONLY` is also removed. Report‑only mode is now activated by populating the `CONTENT_SECURITY_POLICY_REPORT_ONLY` dictionary (and optionally leaving `CONTENT_SECURITY_POLICY` empty or less restrictive).

3. **Django 6.0 native CSP** – Django 6.0 ships with its own CSP middleware (`django.middleware.csp.ContentSecurityPolicyMiddleware`) and settings `SECURE_CSP` / `SECURE_CSP_REPORT_ONLY`. However, your project currently uses `csp.middleware.CSPMiddleware` from django‑csp. The two can coexist, but the immediate error is solely a django‑csp configuration problem.

4. **Django Ninja 1.6.2 compatibility** – Django Ninja 1.5.1+ formally supports Django 6.0, so no conflict there.

---

## 4. Step‑by‑Step Remediation Plan

### 4.1 `base.py` – Remove old‑style settings

**Current state (lines to delete/modify):**

```python
# base.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FONT_SRC = ("'self'",)
CSP_REPORT_ONLY = False
```

**Action:** Delete all the above lines.

**Keep only the dict‑based configuration:**

```python
# base.py – NEW configuration only
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'"],
    }
}

CONTENT_SECURITY_POLICY_REPORT_ONLY = {}   # empty in base; overridden in dev
```

*Note:* Values must be **iterables** (tuples or lists). The migration guide recommends lists.

### 4.2 `development.py` – Override only the dict

**Current state (lines to modify):**

```python
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_REPORT_ONLY = True

CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": CSP_DEFAULT_SRC,   # references old variable
        "script-src": CSP_SCRIPT_SRC,     # references old variable
        "style-src": CSP_STYLE_SRC,       # references old variable
        "img-src": CSP_IMG_SRC,           # references old variable
        "connect-src": CSP_CONNECT_SRC,   # references old variable
        "font-src": CSP_FONT_SRC,         # references old variable
    }
}
CONTENT_SECURITY_POLICY = {}
```

**Action:** Replace with a self‑contained definition:

```python
# development.py – override for report‑only mode
CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'"],
    }
}

CONTENT_SECURITY_POLICY = {}   # no enforced policy in dev
```

### 4.3 Verify and restart

```bash
# 1. Run Django system checks
python manage.py check

# 2. If no errors, restart the server
kill $(cat django.pid) 2>/dev/null
python manage.py runserver 0.0.0.0:8000
```

---

## 5. Optional Future Improvements

* **Switch to Django’s native CSP** – Replace `csp.middleware.CSPMiddleware` with `django.middleware.csp.ContentSecurityPolicyMiddleware` and rename the settings to `SECURE_CSP` / `SECURE_CSP_REPORT_ONLY`. This eliminates the third‑party dependency.

* **Update CSP decorators** – If any views use decorators like `@csp_update`, adjust them to the new dict‑based signature.

---

By following the plan above, the `csp.E001` error will be resolved and the development server will start successfully.

