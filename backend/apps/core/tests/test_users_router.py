"""
TDD tests for users router — validates A and C audit fix requirements.

A: @paginate anti-pattern → manual slice & count pagination
C: Auth dedup → get_authenticated_user() replaces SessionManager direct reads
"""

import inspect
import re
import uuid

import pytest
from django.test import TestCase

from apps.core.tests.factories import EntityFactory, UserFactory


@pytest.mark.django_db
class TestUsersRouterPagination(TestCase):
    """RED phase: list_users must use manual pagination, not @paginate."""

    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity, role='admin')

    # ------------------------------------------------------------------
    # RED-A1: @paginate decorator must not exist in users.py
    # ------------------------------------------------------------------
    def test_paginate_decorator_not_used(self):
        """RED: @paginate decorator is an anti-pattern — must be absent."""
        import apps.core.routers.users as users_module

        with open(users_module.__file__) as fh:
            source = fh.read()

        self.assertNotIn(
            '@paginate', source,
            '@paginate decorator still present in users.py — '
            'replace with manual slice-and-count pagination',
        )

    # ------------------------------------------------------------------
    # RED-A2: list_users source must contain manual pagination logic
    # ------------------------------------------------------------------
    def test_list_users_uses_manual_pagination(self):
        """RED: list_users must implement manual pagination directly."""
        from apps.core.routers.users import list_users

        source = inspect.getsource(list_users)

        # Manual pagination signature signs: page/per_page params in function
        self.assertIn(
            'page', source,
            'list_users missing page parameter — manual pagination required',
        )
        self.assertIn(
            'per_page', source,
            'list_users missing per_page parameter — manual pagination required',
        )

    # ------------------------------------------------------------------
    # RED-A3: The paginate import must be removed
    # ------------------------------------------------------------------
    def test_paginate_import_removed(self):
        """RED: from ninja.pagination import paginate is dead code."""
        import apps.core.routers.users as users_module

        with open(users_module.__file__) as fh:
            source = fh.read()

        self.assertNotIn(
            'from ninja.pagination import paginate',
            source,
            'Unused paginate import still present in users.py',
        )


@pytest.mark.django_db
class TestUsersRouterAuthDedup(TestCase):
    """RED phase: _check_admin_permission must use get_authenticated_user()."""

    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity, role='admin')

    # ------------------------------------------------------------------
    # RED-C1: _check_admin_permission must not import SessionManager
    # ------------------------------------------------------------------
    def test_check_admin_permission_no_direct_session_import(self):
        """RED: _check_admin_permission must not import SessionManager directly."""
        import apps.core.routers.users as users_module

        with open(users_module.__file__) as fh:
            source = fh.read()

        # SessionManager should not be imported anywhere in users.py
        self.assertNotIn(
            'SessionManager', source,
            'SessionManager reference still in users.py — '
            'use get_authenticated_user() helper instead',
        )

    # ------------------------------------------------------------------
    # RED-C2: _check_admin_permission must not import AuthenticationService
    # ------------------------------------------------------------------
    def test_check_admin_permission_no_direct_auth_service_import(self):
        """RED: _check_admin_permission must not import AuthenticationService."""
        import apps.core.routers.users as users_module

        with open(users_module.__file__) as fh:
            source = fh.read()

        self.assertNotIn(
            'AuthenticationService', source,
            'AuthenticationService reference still in users.py — '
            'use get_authenticated_user() helper instead',
        )

    # ------------------------------------------------------------------
    # RED-C3: users.py must import get_authenticated_user at module level
    # ------------------------------------------------------------------
    def test_users_module_imports_get_authenticated_user(self):
        """RED: Module-level import of get_authenticated_user must be present."""
        import apps.core.routers.users as users_module

        self.assertTrue(
            hasattr(users_module, 'get_authenticated_user') or
            'get_authenticated_user' in str(users_module.__dict__),
            'Module-level get_authenticated_user import missing from users.py',
        )

    # ------------------------------------------------------------------
    # RED-C4: _check_admin_permission source calls get_authenticated_user
    # ------------------------------------------------------------------
    def test_check_admin_permission_calls_helper(self):
        """RED: _check_admin_permission must call get_authenticated_user(request)."""
        import apps.core.routers.users as users_module

        source = inspect.getsource(users_module._check_admin_permission)

        self.assertIn(
            'get_authenticated_user(request)', source,
            '_check_admin_permission does not call get_authenticated_user — '
            'must use the helper instead of manual session reads',
        )
        self.assertNotIn(
            'request.COOKIES.get', source,
            '_check_admin_permission still reads cookies directly — '
            'must use get_authenticated_user(request)',
        )
        self.assertNotIn(
            'SessionManager.get_session', source,
            '_check_admin_permission still calls SessionManager directly — '
            'must use get_authenticated_user(request)',
        )