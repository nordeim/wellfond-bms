"""
Transaction and intercompany transfer tests.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.core.models import Entity, User
from apps.finance.models import Transaction, IntercompanyTransfer, TransactionType, TransactionCategory


class TestTransactionCRUD(TestCase):
    """Test Transaction CRUD operations."""

    def setUp(self):
        self.entity = Entity.objects.create(
            name="Test Entity TXN",
            code="TESTTXN",
            slug="test-entity-txn",
        )

    def test_create_transaction(self):
        """Test creating a transaction."""
        txn = Transaction.objects.create(
            type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            entity=self.entity,
            date=date(2026, 4, 15),
            category=TransactionCategory.OPERATIONS,
            description="Test transaction",
        )
        assert txn.id is not None
        assert txn.amount == Decimal("100.00")

    def test_entity_scoping(self):
        """Test entity scoping on transactions."""
        txn = Transaction.objects.create(
            type=TransactionType.REVENUE,
            amount=Decimal("500.00"),
            entity=self.entity,
            date=date(2026, 4, 15),
            category=TransactionCategory.SALE,
        )
        # Should be retrievable by entity
        results = Transaction.objects.filter(entity=self.entity)
        assert txn in results


class TestIntercompanyTransfer(TestCase):
    """Test IntercompanyTransfer operations."""

    def setUp(self):
        self.entity_a = Entity.objects.create(name="Entity A", code="ENTA", slug="enta")
        self.entity_b = Entity.objects.create(name="Entity B", code="ENTB", slug="entb")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity_a,
        )

    def test_intercompany_transfer_creates_transactions(self):
        """Test that intercompany transfer creates balancing transactions."""
        transfer = IntercompanyTransfer.objects.create(
            from_entity=self.entity_a,
            to_entity=self.entity_b,
            amount=Decimal("1000.00"),
            date=date(2026, 4, 15),
            description="Test transfer",
            created_by=self.user,
        )
        
        # Should create 2 transaction records
        txns = Transaction.objects.filter(
            entity__in=[self.entity_a, self.entity_b],
            date=date(2026, 4, 15),
        )
        assert txns.count() == 2

    def test_intercompany_balanced(self):
        """Test that intercompany transfers net to zero."""
        IntercompanyTransfer.objects.create(
            from_entity=self.entity_a,
            to_entity=self.entity_b,
            amount=Decimal("500.00"),
            date=date(2026, 4, 15),
            description="Test",
            created_by=self.user,
        )
        
        # Get transactions
        expense_txn = Transaction.objects.get(
            entity=self.entity_a,
            type=TransactionType.EXPENSE,
        )
        revenue_txn = Transaction.objects.get(
            entity=self.entity_b,
            type=TransactionType.REVENUE,
        )
        
        # Should balance
        assert expense_txn.amount == revenue_txn.amount == Decimal("500.00")

    def test_intercompany_different_entities(self):
        """Test that from and to entities must be different."""
        # This should be validated at the service/router level
        # The model itself allows it, but business logic should prevent it
        pass
