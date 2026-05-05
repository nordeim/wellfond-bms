Now I have full clarity. Here is the analysis and fix.
---
Root Cause Analysis: MED-001 — gst_rate Float Default
The Problem (3 layers)
Layer 1 — Model definition (core/models.py:112-117):
gst_rate = models.DecimalField(
    max_digits=5,
    decimal_places=4,
    default=0.09,  # ← float literal, should be Decimal("0.09")
)
Django stores DecimalField.default as float 0.09 — not a Decimal.
Layer 2 — Runtime crash in agreement.py (sales/services/agreement.py:66):
gst_rate = entity.gst_rate if entity.gst_rate is not None else Decimal("0.09")
# gst_rate is a float (0.09), not a Decimal
# ...
divisor = Decimal("1") + gst_rate  # ← TypeError: unsupported operand type(s) for +: 
When an unsaved Entity() uses the float default, agreement.py mixes Decimal and float arithmetic → TypeError crash.
Layer 3 — Precision loss if someone calls Decimal(entity.gst_rate) instead of Decimal(str(entity.gst_rate)):
Decimal(0.09)   # → Decimal('0.089999999999999996669330926124530...')  WRONG
Decimal("0.09") # → Decimal('0.09')                                    CORRECT
The gst.py service does use Decimal(str(...)) (line 54), which happens to work. But any new code path that does the natural thing of Decimal(entity.gst_rate) will get silently wrong values.
Layer 4 — Schema layer (core/schemas.py:144,162): EntityResponse and EntityCreate also use float type for gst_rate, which could compound the precision issue at the API boundary.
← Edit backend/apps/core/models.py
# Singapore GST rate (default 9%)
gst_rate = models.DecimalField(
    max_digits=5,
    decimal_places=4,
    default=0.09,
    help_text="GST rate as decimal (e.g., 0.09 for 9%)",
)
# Contact
# Singapore GST rate (default 9%)
gst_rate = models.DecimalField(
    max_digits=5,
    decimal_places=4,
    default=Decimal("0.09"),
    help_text="GST rate as decimal (e.g., 0.09 for 9%)",
)
# Contact

→ Read backend/apps/core/models.py [offset=1, limit=10]
Need
← Edit backend/apps/core/models.py
User model with RBAC and entity-based access control
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

User model with RBAC and entity-based access control
"""
import uuid
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models

Now fix the two downstream locations that use float
→ Read backend/apps/core/schemas.py [limit=15, offset=1]
→ Read backend/apps/core/schemas.py [limit=20, offset=135]
The EntityResponse.gst_rate: float is less critical because Pydantic's from_attributes=True reads from the ORM's Decimal and converts to float for JSON — but this risks precision loss at the API boundary for financial data. However, given decimal_places=4, the float 0.09 is exactly representable in float64 (it's the construction from float literal that causes issues, not float64 representation of simple decimals
# Check Decimal->float->Decimal roundtrip precision
$ python3 -c "
from decimal import Decimal
# 0.09 is NOT exactly representable
print(f'float64 0.09 exact: {0.09:.30f}')
# But Decimal('0.09') -> float -> back to Decimal might lose precision
print(f'round-trip: {Decimal(str(float(Decimal(\"0.09\"))))}')
# For 4 decimal places: 0.0912, 0.1234, etc
for v in ['0.09', '0.0900', '0.0912', '0.00']:
    d = Decimal(v)
    f = float(d)
    print(f'{v:>8s} -> float: {f:.20f} -> back: {Decimal(str(f))}')
"
float64 0.09 exact: 0.089999999999999996669330926125
round-trip: 0.09
    0.09 -> float: 0.08999999999999999667 -> back: 0.09
  0.0900 -> float: 0.08999999999999999667 -> back: 0.09
  0.0912 -> float: 0.09120000000000000329 -> back: 0.0912
    0.00 -> float: 0.00000000000000000000 -> back: 0.0

OK — for a Decimal(4) field with simple rates like 0.09, the Decimal → float round-trip via str() is lossless. The schema float type is acceptable for JSON serialization. The critical fix is the model default. Let me also fix the conftest.py and factory
→ Read backend/conftest.py [limit=10, offset=43]
→ Read backend/apps/core/tests/factories.py [limit=15, offset=18]
The factory and conftest both use float literals for gst_rate. These will be saved to the DB correctly by Django (it converts float→Decimal during get_prep_value), so they're not broken, but they're inconsistent and violate the AGENTS.md mandate to use
← Edit backend/conftest.py
        "name": "Holdings",
        "slug": "holdings",
        "is_active": True,
        "is_holding": True,
        "gst_rate": 0.09,
    },
)
return entity
        "name": "Holdings",
        "slug": "holdings",
        "is_active": True,
        "is_holding": True,
        "gst_rate": Decimal("0.09"),
    },
)
return entity
← Edit backend/apps/core/tests/factories.py
slug = factory.LazyAttribute(lambda obj: obj.code.lower())
is_active = True
is_holding = factory.LazyAttribute(lambda obj: obj.code == Entity.Code.HOLDINGS)
gst_rate = factory.LazyAttribute(
    lambda obj: 0.00 if obj.code == Entity.Code.THOMSON else 0.09
)
address = factory.Faker('address')
phone = factory.Faker('bothify', text='+65 6### ####')
email = factory.Faker('company_email')
slug = factory.LazyAttribute(lambda obj: obj.code.lower())
is_active = True
is_holding = factory.LazyAttribute(lambda obj: obj.code == Entity.Code.HOLDINGS)
gst_rate = factory.LazyAttribute(
    lambda obj: Decimal("0.00") if obj.code == Entity.Code.THOMSON else Decimal("0.09")
)
address = factory.Faker('address')
phone = factory.Faker('bothify', text='+65 6### ####')
email = factory.Faker('company_email')

# Check if Decimal is imported in conftest.py
$ grep -n 'Decimal' /home/project/wellfond-bms/backend/conftest.py | head -5
48:            "gst_rate": Decimal("0.09"),
# Check if Decimal is imported in factories.py
$ grep -n 'Decimal' /home/project/wellfond-bms/backend/apps/core/tests/factories.py | head -5
25:        lambda obj: Decimal("0.00") if obj.code == Entity.Code.THOMSON else Decimal("0.09")
Both files need Decimal imports. Let me check
→ Read backend/conftest.py [limit=10, offset=1]
→ Read backend/apps/core/tests/factories.py [limit=10, offset=1]
← Edit backend/conftest.py
Replaces force_login() which breaks Ninja routers.
"""
import pytest
from django.http import HttpRequest
from apps.core.models import Entity, User
Replaces force_login() which breaks Ninja routers.
"""
import pytest
from decimal import Decimal
from django.http import HttpRequest
from apps.core.models import Entity, User
← Edit backend/apps/core/tests/factories.py
Factories for creating test data for core models.
"""
import factory
from factory import Faker
from apps.core.models import User, Entity
Factories for creating test data for core models.
"""
import factory
from decimal import Decimal
from factory import Faker
from apps.core.models import User, Entity

Now fix the test_rate_limit.py and test_gst_fix.py — they also
→ Read backend/apps/core/tests/test_rate_limit.py [limit=5, offset=22]
# Check gst_rate usage in rate limit tests
$ grep -n 'gst_rate' /home/project/wellfond-bms/backend/apps/core/tests/test_rate_limit.py
28:            gst_rate=0.09
← Edit backend/apps/core/tests/test_rate_limit.py
# Create test entity and user
self.entity = Entity.objects.create(
    name="Test Entity",
    code="TEST",
    gst_rate=0.09
)
self.user = User.objects.create_user(
    email="test@example.com",
    password="TestPass123!",
# Create test entity and user
self.entity = Entity.objects.create(
    name="Test Entity",
    code="TEST",
    gst_rate=Decimal("0.09")
)
self.user = User.objects.create_user(
    email="test@example.com",
    password="TestPass123!",
Now verify the other `test_gst_fix.py
# Check gst_rate usage in gst fix tests
$ grep -n 'gst_rate.*0\.' /home/project/wellfond-bms/backend/apps/sales/tests/test_gst_fix.py
31:            gst_rate=Decimal("0.00")  # 0% GST
39:            f"Expected 0.00 GST for entity with gst_rate=0.00, "
49:            gst_rate=Decimal("0.09")
66:            gst_rate=Decimal("0.09")
85:            gst_rate=Decimal("0.00")
101:            gst_rate=Decimal("0.07")
test_gst_fix.py already correctly uses Decimal("0.09") — no change needed there. But I notice it uses gst_rate=Decimal("0.07") on line 101 — this tests a rate that's not the default, which is good.
# Verify Decimal default for gst_rate in /home/project/wellfond-bms/backend
$ DJANGO_SETTINGS_MODULE=config.settings.development python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from decimal import Decimal
from apps.core.models import Entity
# Test 1: Model default is now Decimal
f = Entity._meta.get_field('gst_rate')
default_val = f.get_default()
print(f'Test 1 - get_default(): {default_val!r} type={type(default_val).__name__}')
assert isinstance(default_val, Decimal), f'Expected Decimal, got {type(default_val)}'
print('  PASS')
# Test 2: Unsaved entity has Decimal, not float
e = Entity(name='X', code='X', slug='x-1')
print(f'Test 2 - e.gst_rate: {e.gst_rate!r} type={type(e.gst_rate).__name__}')
assert isinstance(e.gst_rate, Decimal), f'Expected Decimal, got {type(e.gst_rate)}'
assert e.gst_rate == Decimal('0.09'), f'Expected 0.09, got {e.gst_rate}'
print('  PASS')
# Test 3: Decimal + Decimal works (agreement.py path)
gst_rate = e.gst_rate if e.gst_rate is not None else Decimal('0.09')
divisor = Decimal('1') + gst_rate
print(f'Test 3 - divisor: {divisor!r}')
assert divisor == Decimal('1.09'), f'Expected 1.09, got {divisor}'
print('  PASS')
# Test 4: GST calculation produces correct result
price = Decimal('109.00')
gst = price * gst_rate / divisor
result = gst.quantize(Decimal('0.01'))
print(f'Test 4 - GST on 109 at 9%: {result}')
assert result == Decimal('9.00'), f'Expected 9.00, got {result}'
print('  PASS')
# Test 5: Thomson at 0%
e2 = Entity(name='T', code='THOMSON', slug='thomson', gst_rate=Decimal('0.00'))
gst_rate2 = e2.gst_rate if e2.gst_rate is not None else Decimal('0.09')
assert gst_rate2 == Decimal('0.00')
print(f'Test 5 - Thomson 0%: {gst_rate2} PASS')
print()
print('All 5 tests PASSED')
"
Test 1 - get_default(): Decimal('0.09') type=Decimal
  PASS
Test 2 - e.gst_rate: Decimal('0.09') type=Decimal
  PASS
Test 3 - divisor: Decimal('1.09')
  PASS
Test 4 - GST on 109 at 9%: 9.00
  PASS
Test 5 - Thomson 0%: 0.00 PASS
…

$ python -m pytest apps/core/ apps/compliance/ apps/sales/ -v --tb=short 2>&1 | grep -E '(PASSED|FAILED|ERROR|passed|failed|error)' | tail -30

# Run core integration tests in /home/project/wellfond-bms/backend
$ python -m pytest apps/core/tests/test_dashboard.py apps/core/tests/test_pdpa_enforcement.py apps/core/tests/test_permissions.py --no-header --tb=line 2>&1 | tail -15
FAILED apps/core/tests/test_permissions.py::TestPDPAEnforcement::test_enforce_pdpa_filters_without_consent
FAILED apps/core/tests/test_permissions.py::TestPDPAEnforcement::test_enforce_pdpa_preserves_other_filters
ERROR apps/core/tests/test_permissions.py::TestScopeEntity::test_scope_entity_excludes_other_entity
ERROR apps/core/tests/test_permissions.py::TestScopeEntity::test_scope_entity_allows_management_all_entities
ERROR apps/core/tests/test_permissions.py::TestCrossEntityAccess::test_admin_cannot_access_other_entity
ERROR apps/core/tests/test_permissions.py::TestCrossEntityAccess::test_sales_cannot_access_other_entity
ERROR apps/core/tests/test_permissions.py::TestCrossEntityAccess::test_ground_cannot_access_other_entity
ERROR apps/core/tests/test_permissions.py::TestRequireRoleDecorator::test_require_role_allows_authorized_user
ERROR apps/core/tests/test_permissions.py::TestRequireRoleDecorator::test_require_role_denies_unauthorized_user
ERROR apps/core/tests/test_permissions.py::TestRequireRoleDecorator::test_require_role_allows_management_any_role
…

# Show final diff of all changes
$ git diff HEAD -- backend/apps/core/models.py backend/conftest.py backend/apps/core/tests/factories.py backend/apps/core/tests/test_rate_limit.py
diff --git a/backend/apps/core/models.py b/backend/apps/core/models.py
index b770b91..0b8eaf6 100644
--- a/backend/apps/core/models.py
+++ b/backend/apps/core/models.py
@@ -5,6 +5,7 @@ User model with RBAC and entity-based access control
 """
 
 import uuid
+from decimal import Decimal
 from django.contrib.auth.models import AbstractUser
…

