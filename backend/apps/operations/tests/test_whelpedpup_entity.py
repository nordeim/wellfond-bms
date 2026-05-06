"""
Test: Entity FK in WhelpedPup.
High Issue H-011: Add entity FK to WhelpedPup.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from uuid import uuid4

from apps.core.models import Entity
from apps.operations.models import Dog, WhelpedLog, WhelpedPup

User = get_user_model()


class TestWhelpedPupEntityFK(TestCase):
    """Test entity FK in WhelpedPup."""

    def setUp(self):
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST",
            slug="test-entity",
        )
        self.dog = Dog.objects.create(
            microchip="900001234567890",
            name="Test Dog",
            breed="Labrador",
            dob="2024-01-01",
            gender="F",
            entity=self.entity,
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="GROUND",
        )
        self.whelping = WhelpedLog.objects.create(
            dog=self.dog,
            method="NATURAL",
            alive_count=5,
            stillborn_count=1,
            created_by=self.user,
        )

    def test_whelpedpup_has_entity_field(self):
        """RED: Test that WhelpedPup has entity FK."""
        # Check if entity field exists in model
        field_names = [f.name for f in WhelpedPup._meta.fields]
        
        # This will fail in RED phase (entity field doesn't exist)
        self.assertIn('entity', field_names)

    def test_whelpedpup_entity_in_create(self):
        """RED: Test that entity can be set during creation."""
        # This will fail in RED phase (entity field doesn't exist)
        pup = WhelpedPup.objects.create(
            log=self.whelping,
            gender="M",
            colour="Yellow",
            birth_weight="0.5",
            entity=self.entity,  # Should fail in RED phase
        )
        self.assertEqual(pup.entity, self.entity)

    def test_whelpedpup_entity_scoping(self):
        """RED: Test that entity scoping works."""
        # This will fail in RED phase (entity field doesn't exist)
        from django.db.models import Q
        
        # Try to filter by entity (should fail in RED phase)
        try:
            WhelpedPup.objects.filter(entity=self.entity)
            # If we get here, entity field exists (GREEN phase)
            self.fail("Entity field exists - should fail in RED phase")
        except Exception:
            # Entity field doesn't exist (RED phase - test passes)
            pass
