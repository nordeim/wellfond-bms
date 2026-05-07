"""Test FIN-005: Finance models must use `on_delete=PROTECT` on Entity/User FKs.

FIX-05: Per AGENTS.md anti-pattern table, Entity and User FKs must use
`PROTECT` not `CASCADE` to prevent accidental data loss.
"""
from django.test import TestCase

from apps.finance.models import Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot


class TestFinanceEntityFKProtection(TestCase):
    """Verify all Entity/User FKs use on_delete=PROTECT."""

    def test_transaction_entity_is_protected(self):
        """Transaction.entity must use PROTECT."""
        field = Transaction._meta.get_field("entity")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_intercompany_from_entity_is_protected(self):
        """IntercompanyTransfer.from_entity must use PROTECT."""
        field = IntercompanyTransfer._meta.get_field("from_entity")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_intercompany_to_entity_is_protected(self):
        """IntercompanyTransfer.to_entity must use PROTECT."""
        field = IntercompanyTransfer._meta.get_field("to_entity")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_intercompany_created_by_is_protected(self):
        """IntercompanyTransfer.created_by must use PROTECT."""
        field = IntercompanyTransfer._meta.get_field("created_by")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_gst_report_entity_is_protected(self):
        """GSTReport.entity must use PROTECT."""
        field = GSTReport._meta.get_field("entity")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_gst_report_generated_by_is_protected(self):
        """GSTReport.generated_by must use PROTECT."""
        field = GSTReport._meta.get_field("generated_by")
        assert field.remote_field.on_delete.__name__ == "PROTECT"

    def test_pnl_snapshot_entity_is_protected(self):
        """PNLSnapshot.entity must use PROTECT."""
        field = PNLSnapshot._meta.get_field("entity")
        assert field.remote_field.on_delete.__name__ == "PROTECT"
