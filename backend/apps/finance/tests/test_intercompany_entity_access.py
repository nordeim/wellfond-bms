"""
Test: Entity access check in IntercompanyTransfer.
High Issue H-003: Add entity access check to IntercompanyTransfer.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from ninja.errors import HttpError
from unittest.mock import MagicMock
from datetime import date

from apps.core.models import Entity
from apps.finance.models import IntercompanyTransfer
from apps.finance.schemas import IntercompanyCreate

User = get_user_model()


class TestIntercompanyTransferEntityAccess(TestCase):
    """Test entity access check in IntercompanyTransfer."""

    def setUp(self):
        self.entity_a = Entity.objects.create(
            name="Entity A",
            code="ENTA",
            slug="entity-a",
        )
        self.entity_b = Entity.objects.create(
            name="Entity B",
            code="ENTB",
            slug="entity-b",
        )
        self.entity_c = Entity.objects.create(
            name="Entity C",
            code="ENTC",
            slug="entity-c",
        )

        self.user_finance_a = User.objects.create_user(
            username="finance_a",
            email="finance_a@test.com",
            password="testpass123",
            entity=self.entity_a,
            role="FINANCE",
        )
        
        self.user_management = User.objects.create_user(
            username="management",
            email="management@test.com",
            password="testpass123",
            entity=self.entity_a,
            role="MANAGEMENT",
        )

    def test_finance_cannot_create_transfer_involving_other_entities(self):
        """Test that FINANCE user cannot create transfer without their entity."""
        # Mock request with finance user
        request = MagicMock()
        request.user = self.user_finance_a
        
        # Try to create transfer from entity_b to entity_c (user has no access)
        payload = IntercompanyCreate(
            from_entity_id=self.entity_b.id,
            to_entity_id=self.entity_c.id,
            amount=Decimal("1000.00"),
            date=date(2026, 5, 6),
            description="Unauthorized transfer",
        )
        
        # Call the endpoint - should raise HttpError
        from apps.finance.routers.reports import create_intercompany_transfer
        
        with self.assertRaises(HttpError) as context:
            create_intercompany_transfer(request, payload)
        
        # Verify error status
        self.assertEqual(context.exception.status_code, 403)

    def test_finance_can_create_transfer_involving_their_entity(self):
        """Test that FINANCE user can create transfer involving their entity."""
        request = MagicMock()
        request.user = self.user_finance_a
        
        # Transfer from entity_a (user's entity) to entity_b
        payload = IntercompanyCreate(
            from_entity_id=self.entity_a.id,
            to_entity_id=self.entity_b.id,
            amount=Decimal("500.00"),
            date=date(2026, 5, 6),
            description="Authorized transfer",
        )
        
        # This should succeed
        response = create_intercompany_transfer(request, payload)
        self.assertIsNotNone(response)
        self.assertEqual(response.from_entity_id, self.entity_a.id)

    def test_management_can_create_transfer_any_entity(self):
        """Test that MANAGEMENT user can create transfer between any entities."""
        request = MagicMock()
        request.user = self.user_management
        
        payload = IntercompanyCreate(
            from_entity_id=self.entity_b.id,
            to_entity_id=self.entity_c.id,
            amount=Decimal("1000.00"),
            date=date(2026, 5, 6),
            description="Management transfer",
        )
        
        # This should succeed (MANAGEMENT can access all entities)
        response = create_intercompany_transfer(request, payload)
        self.assertIsNotNone(response)
        self.assertEqual(response.from_entity_id, self.entity_b.id)
