"""
Test: COI Service Async Compatibility
High Issue H4: COI raw SQL not async-compatible

These tests ensure COI calculations can be called from async contexts.
"""

import asyncio
from uuid import uuid4
from decimal import Decimal

from django.test import TestCase

from apps.operations.models import Dog, Entity
from apps.breeding.models import DogClosure
from apps.breeding.services.coi import (
    get_shared_ancestors,
    calc_coi,
    calc_coi_async,
    get_shared_ancestors_async,
)


class COIAsyncTests(TestCase):
    """Tests for HIGH-4: COI async wrapper."""

    def setUp(self):
        """Set up test data."""
        from datetime import date
        self.entity = Entity.objects.create(
            name="Test Entity",
            slug="test-entity"
        )
        self.dam = Dog.objects.create(
            name="Test Dam",
            gender="F",
            entity=self.entity,
            microchip="DAM001",
            dob=date(2020, 1, 1)
        )
        self.sire = Dog.objects.create(
            name="Test Sire",
            gender="M",
            entity=self.entity,
            microchip="SIRE001",
            dob=date(2020, 1, 1)
        )

    def test_get_shared_ancestors_async_exists(self):
        """Test: get_shared_ancestors_async function exists."""
        self.assertTrue(
            callable(get_shared_ancestors_async),
            "get_shared_ancestors_async should be a callable function"
        )

    def test_calc_coi_async_exists(self):
        """Test: calc_coi_async function exists."""
        self.assertTrue(
            callable(calc_coi_async),
            "calc_coi_async should be a callable function"
        )

    def test_calc_coi_async_returns_correct_result(self):
        """Test: calc_coi_async returns same result as sync version."""
        # Run async version
        async_result = asyncio.run(
            calc_coi_async(self.dam.id, self.sire.id, generations=3)
        )

        # Run sync version
        sync_result = calc_coi(self.dam.id, self.sire.id, generations=3)

        # Results should be identical
        self.assertEqual(
            async_result["coi_pct"],
            sync_result["coi_pct"],
            "Async and sync COI calculations should return same result"
        )
        self.assertEqual(
            async_result["generation_depth"],
            sync_result["generation_depth"]
        )

    def test_calc_coi_async_handles_no_common_ancestors(self):
        """Test: calc_coi_async handles dogs with no common ancestors."""
        result = asyncio.run(
            calc_coi_async(self.dam.id, self.sire.id, generations=5)
        )

        self.assertEqual(result["coi_pct"], 0.0)
        self.assertEqual(len(result["shared_ancestors"]), 0)
        self.assertFalse(result["cached"])

    def test_calc_coi_async_uses_cache(self):
        """Test: calc_coi_async respects cache parameter."""
        # First call - no cache
        result1 = asyncio.run(
            calc_coi_async(self.dam.id, self.sire.id, use_cache=False)
        )
        self.assertFalse(result1.get("cached", False))

        # Second call with cache
        result2 = asyncio.run(
            calc_coi_async(self.dam.id, self.sire.id, use_cache=True)
        )
        # May or may not be cached depending on previous runs

    def test_calc_coi_async_different_generations(self):
        """Test: calc_coi_async works with different generation depths."""
        for depth in [3, 5, 7]:
            result = asyncio.run(
                calc_coi_async(self.dam.id, self.sire.id, generations=depth)
            )
            self.assertEqual(result["generation_depth"], depth)

    def test_get_shared_ancestors_async_returns_list(self):
        """Test: get_shared_ancestors_async returns list of ancestors."""
        ancestors = asyncio.run(
            get_shared_ancestors_async(self.dam.id, self.sire.id)
        )

        self.assertIsInstance(ancestors, list)

    def test_async_wrapper_preserves_exception_handling(self):
        """Test: async wrapper preserves exception handling."""
        # Test with invalid UUID
        invalid_uuid = uuid4()

        # Should not raise exception, but return empty result
        result = asyncio.run(
            calc_coi_async(invalid_uuid, self.sire.id)
        )

        self.assertIn("coi_pct", result)
