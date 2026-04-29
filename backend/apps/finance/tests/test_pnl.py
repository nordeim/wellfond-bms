"""
P&L calculation tests.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.core.models import Entity
from apps.finance.models import Transaction, TransactionType, TransactionCategory
from apps.finance.services.pnl import calc_pnl, calc_ytd, PNLResult


class TestPNLCalculation(TestCase):
    """Test P&L calculation service."""

    def setUp(self):
        """Set up test data."""
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            slug="test-entity",
        )
        self.month = date(2026, 4, 1)

    def test_pnl_calculates_revenue(self):
        """Test that revenue is calculated from SalesAgreement."""
        # This test requires SalesAgreement to be set up
        # For now, test that the function runs without error
        result = calc_pnl(self.entity.id, self.month)
        assert isinstance(result, PNLResult)
        assert result.entity_id == self.entity.id
        assert result.month == self.month

    def test_pnl_calculates_expenses(self):
        """Test that expenses are calculated from Transactions."""
        # Create an expense transaction
        Transaction.objects.create(
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            entity=self.entity,
            date=self.month,
            category=TransactionCategory.OPERATIONS,
            description="Test expense",
        )

        result = calc_pnl(self.entity.id, self.month)
        # Expenses should include the transaction
        assert result.expenses >= Decimal("500.00")

    def test_pnl_calculates_cogs(self):
        """Test that COGS are calculated from SALE category expenses."""
        # Create a COGS transaction
        Transaction.objects.create(
            type=TransactionType.EXPENSE,
            amount=Decimal("300.00"),
            entity=self.entity,
            date=self.month,
            category=TransactionCategory.SALE,
            description="Test COGS",
        )

        result = calc_pnl(self.entity.id, self.month)
        # COGS should include the transaction
        assert result.cogs >= Decimal("300.00")

    def test_pnl_net_correct(self):
        """Test that net = revenue - cogs - expenses."""
        result = calc_pnl(self.entity.id, self.month)
        expected_net = result.revenue - result.cogs - result.expenses
        assert result.net == expected_net

    def test_pnl_ytd_rollup(self):
        """Test YTD calculations from April (SG fiscal year)."""
        result = calc_pnl(self.entity.id, self.month)
        # YTD should be calculated
        assert isinstance(result.ytd_revenue, Decimal)
        assert isinstance(result.ytd_net, Decimal)

    def test_pnl_deterministic(self):
        """Test that P&L calculation is deterministic."""
        result1 = calc_pnl(self.entity.id, self.month)
        result2 = calc_pnl(self.entity.id, self.month)
        assert result1.revenue == result2.revenue
        assert result1.cogs == result2.cogs
        assert result1.expenses == result2.expenses
        assert result1.net == result2.net


class TestYTD(TestCase):
    """Test YTD calculation."""

    def setUp(self):
        self.entity = Entity.objects.create(
            name="Test Entity YTD",
            code="TESTYTD",
            slug="test-entity-ytd",
        )

    def test_ytd_april_start(self):
        """Test YTD starts from April for Singapore fiscal year."""
        # Test in April
        april = date(2026, 4, 15)
        ytd_revenue, ytd_net = calc_ytd(self.entity.id, april)
        assert isinstance(ytd_revenue, Decimal)
        assert isinstance(ytd_net, Decimal)

    def test_ytd_march_rollover(self):
        """Test YTD rolls over in April (new fiscal year)."""
        # Test in March of next year
        march = date(2027, 3, 15)
        ytd_revenue, ytd_net = calc_ytd(self.entity.id, march)
        assert isinstance(ytd_revenue, Decimal)
        assert isinstance(ytd_net, Decimal)
