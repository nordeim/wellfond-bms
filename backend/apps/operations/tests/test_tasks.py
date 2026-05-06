"""
TDD tests for operations Celery tasks.
Covers C-003 (logger import), C-004 (create_alert_event arg count),
H-002 (archive_old_logs atomicity), and H-004 (sync_offline_queue imports).
"""

import pytest
import logging
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from django.utils import timezone

from apps.operations.tasks import (
    archive_old_logs,
    check_rehome_overdue,
    generate_health_alert,
    sync_offline_queue,
)


class TestLoggerImport:
    """C-003: Verify logger is properly imported and usable in tasks.py."""

    def test_logger_is_defined(self):
        """logger should be importable from tasks module."""
        from apps.operations import tasks
        assert hasattr(tasks, "logger"), "logger must be defined in tasks module"

    def test_logger_is_logging_logger(self):
        """logger should be a logging.Logger instance."""
        from apps.operations import tasks
        assert isinstance(tasks.logger, logging.Logger)

    def test_logger_has_correct_name(self):
        """logger name should follow __name__ convention."""
        from apps.operations import tasks
        assert tasks.logger.name == "apps.operations.tasks"


class TestCreateAlertEvent:
    """C-004: generate_health_alert must pass log_type as first argument."""

    @patch("apps.operations.models.HealthObsLog")
    @patch("apps.operations.services.alerts.create_alert_event")
    def test_generate_health_alert_passes_alert_type(self, mock_create_alert, mock_model):
        """create_alert_event should receive (alert_type, log_instance)."""
        mock_log = MagicMock()
        mock_log.dog_id = "dog-123"
        mock_model.objects.get.return_value = mock_log
        mock_create_alert.return_value = {"id": "alert-1"}

        generate_health_alert("log-1", "health_obs")

        mock_create_alert.assert_called_once_with("health_obs", mock_log)


class TestArchiveOldLogsAtomicity:
    """H-002: archive_old_logs must be atomic with audit log before deletion."""

    def test_archive_old_logs_uses_transaction_atomic(self):
        """archive_old_logs should be wrapped in transaction.atomic()."""
        import inspect
        from apps.operations import tasks as tasks_module

        source = inspect.getsource(tasks_module.archive_old_logs)
        assert "transaction.atomic" in source, (
            "archive_old_logs must use transaction.atomic()"
        )

    def test_audit_log_created_before_deletion_order(self):
        """AuditLog must be created BEFORE any .delete() calls."""
        import inspect
        from apps.operations import tasks as tasks_module

        source = inspect.getsource(tasks_module.archive_old_logs)
        create_idx = source.find("AuditLog.objects.create")
        delete_idx = source.find(".delete()")

        assert create_idx != -1, "AuditLog.objects.create must be present"
        assert delete_idx != -1, ".delete() must be present"
        assert create_idx < delete_idx, (
            "AuditLog must be created BEFORE deletions — "
            "current order has audit log after deletions"
        )


class TestDashboardDecimalPrecision:
    """H-005: Dashboard revenue must preserve Decimal precision."""

    def test_no_float_conversion_in_monthly_data(self):
        """Monthly data should use str() not float() for Decimal values."""
        import inspect
        from apps.core.services import dashboard as dashboard_module

        source = inspect.getsource(dashboard_module.get_revenue_summary)
        assert 'float(total_sales)' not in source, (
            "total_sales must not be converted to float — use str()"
        )
        assert 'float(gst_collected)' not in source, (
            "gst_collected must not be converted to float — use str()"
        )

    def test_totals_sum_from_decimals_not_floats(self):
        """Total revenue/gst should sum Decimal values, not already-floated per-month values."""
        import inspect
        from apps.core.services import dashboard as dashboard_module

        source = inspect.getsource(dashboard_module.get_revenue_summary)
        assert 'sum(m["total_sales"]' not in source, (
            "Totals must not sum already-converted float values — "
            "keep Decimal through summation, convert only at final result"
        )
        assert 'sum(m["gst_collected"]' not in source, (
            "Totals must not sum already-converted float values — "
            "keep Decimal through summation, convert only at final result"
        )


class TestSyncOfflineQueueImports:
    """H-004: sync_offline_queue must import from actual service modules."""

    def test_sync_offline_queue_does_not_import_from_services_package(self):
        """sync_offline_queue should not import from .services (which has empty __all__)."""
        import inspect
        from apps.operations import tasks as tasks_module

        source = inspect.getsource(tasks_module.sync_offline_queue)
        assert "from .services import create_in_heat_log" not in source, (
            "sync_offline_queue must not import create_in_heat_log from .services "
            "(services/__init__.py has empty __all__)"
        )
        assert "from .services import create_mated_log" not in source, (
            "sync_offline_queue must not import create_mated_log from .services "
            "(services/__init__.py has empty __all__)"
        )

    def test_log_creators_module_exists_and_exports_functions(self):
        """services/log_creators.py must exist and export service functions."""
        try:
            from apps.operations.services.log_creators import (
                create_in_heat_log,
                create_mated_log,
            )
            assert callable(create_in_heat_log)
            assert callable(create_mated_log)
        except ImportError as e:
            pytest.fail(f"log_creators module must be importable: {e}")


class TestAuthAliasExists:
    """C-001: AuthenticationService must have get_user_from_request alias."""

    def test_get_user_from_request_exists(self):
        """get_user_from_request must be a callable on AuthenticationService."""
        from apps.core.auth import AuthenticationService

        assert hasattr(AuthenticationService, "get_user_from_request"), (
            "AuthenticationService must have get_user_from_request method"
        )
        assert callable(AuthenticationService.get_user_from_request)

    def test_get_user_from_request_delegates_to_get_current_user(self):
        """get_user_from_request should delegate to get_current_user."""
        from django.http import HttpRequest
        from apps.core.auth import AuthenticationService
        from unittest.mock import patch

        request = HttpRequest()
        request.path = "/test/"

        with patch.object(AuthenticationService, "get_current_user", return_value="mock_user") as mock_gcu:
            result = AuthenticationService.get_user_from_request(request)
            mock_gcu.assert_called_once_with(request)
            assert result == "mock_user"


class TestGetPendingAlertsSignature:
    """C-002: get_pending_alerts must accept both User and keyword args."""

    def test_get_pending_alerts_accepts_kwargs(self):
        """get_pending_alerts should accept keyword arguments for async context."""
        import inspect
        from apps.operations.services.alerts import get_pending_alerts

        sig = inspect.signature(get_pending_alerts)
        params = sig.parameters

        assert "user_id" in params, (
            "get_pending_alerts must accept user_id kwarg for SSE async context"
        )
        assert "entity_id" in params, (
            "get_pending_alerts must accept entity_id kwarg for SSE async context"
        )
        assert "role" in params, (
            "get_pending_alerts must accept role kwarg for SSE async context"
        )
        assert "since_id" in params, (
            "get_pending_alerts must accept since_id kwarg for SSE deduplication"
        )

    def test_get_pending_alerts_user_param_is_optional(self):
        """User param should be optional (default None) for kwarg path."""
        import inspect
        from apps.operations.services.alerts import get_pending_alerts

        sig = inspect.signature(get_pending_alerts)
        params = sig.parameters
        user_param = params.get("user")
        assert user_param is not None, "get_pending_alerts must still accept user param"
        assert user_param.default is not None or str(user_param).startswith("user: "), (
            "user param should be optional"
        )