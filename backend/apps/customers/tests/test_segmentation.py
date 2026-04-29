"""Segmentation Tests
====================
Phase 7: Customer DB & Marketing Blast

Tests for customer segmentation with PDPA enforcement.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from django.test import TestCase
from django.core.cache import cache

from apps.core.models import Entity, User
from apps.customers.models import Customer, HousingType
from apps.customers.services.segmentation import SegmentationService


class TestSegmentationFilters(TestCase):
    """Test segmentation with various filters."""

    def setUp(self):
        """Set up test data."""
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )

        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="admin",
        )

        # Create test customers
        self.customer_hdb = Customer.objects.create(
            name="HDB Customer",
            mobile="+6590000001",
            email="hdb@example.com",
            housing_type=HousingType.HDB,
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        self.customer_condo = Customer.objects.create(
            name="Condo Customer",
            mobile="+6590000002",
            email="condo@example.com",
            housing_type=HousingType.CONDO,
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

        self.customer_landed = Customer.objects.create(
            name="Landed Customer",
            mobile="+6590000003",
            email="landed@example.com",
            housing_type=HousingType.LANDED,
            pdpa_consent=False,  # Opted out
            entity=self.entity,
            created_by=self.user,
        )

        self.customer_no_consent = Customer.objects.create(
            name="No Consent",
            mobile="+6590000004",
            email="noconsent@example.com",
            housing_type=HousingType.HDB,
            pdpa_consent=False,
            entity=self.entity,
            created_by=self.user,
        )

    def test_segment_by_housing_type(self):
        """Test filtering by housing type."""
        filters = {"housing_type": "HDB", "pdpa": True}
        queryset = SegmentationService.build_segment(filters)

        # Should return only HDB customers with PDPA consent
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, "HDB Customer")

    def test_segment_by_entity(self):
        """Test filtering by entity."""
        filters = {"entity_id": str(self.entity.id), "pdpa": True}
        queryset = SegmentationService.build_segment(filters)

        # Should return all consented customers
        self.assertEqual(queryset.count(), 2)

    def test_segment_excludes_pdpa_false(self):
        """Test that PDPA=false customers are excluded."""
        filters = {"pdpa": True}
        queryset = SegmentationService.build_segment(filters)

        # Should only return customers with pdpa_consent=True
        self.assertEqual(queryset.count(), 2)

        # Verify excluded customers
        ids = list(queryset.values_list("name", flat=True))
        self.assertIn("HDB Customer", ids)
        self.assertIn("Condo Customer", ids)
        self.assertNotIn("Landed Customer", ids)
        self.assertNotIn("No Consent", ids)

    def test_segment_combines_filters(self):
        """Test combining multiple filters."""
        filters = {
            "housing_type": "HDB",
            "entity_id": str(self.entity.id),
            "pdpa": True,
        }
        queryset = SegmentationService.build_segment(filters)

        # Should return HDB + consented + entity match
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, "HDB Customer")

    def test_segment_pdpa_false_override(self):
        """Test that pdpa=False can be overridden."""
        filters = {"pdpa": False}  # Override to include non-consented
        queryset = SegmentationService.build_segment(filters)

        # Should return all 4 customers
        self.assertEqual(queryset.count(), 4)

    def test_preview_returns_count(self):
        """Test that preview returns count without fetching data."""
        filters = {"pdpa": True}

        # Clear cache first
        cache.clear()

        count = SegmentationService.preview_segment(filters)
        self.assertEqual(count, 2)

    def test_cached_count(self):
        """Test that segment count is cached."""
        filters = {"pdpa": True}

        # Clear cache
        cache.clear()

        # First call - should hit DB
        count1 = SegmentationService.preview_segment(filters)
        self.assertEqual(count1, 2)

        # Second call - should hit cache
        count2 = SegmentationService.preview_segment(filters)
        self.assertEqual(count2, 2)

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        filters = {"pdpa": True}

        # Clear and set cache
        cache.clear()
        SegmentationService.preview_segment(filters)

        # Invalidate cache
        SegmentationService.invalidate_cache(filters)

        # Verify cache was cleared
        cache_key = SegmentationService._get_cache_key(filters)
        self.assertIsNone(cache.get(cache_key))

    def test_validate_filters_valid(self):
        """Test filter validation with valid filters."""
        filters = {"housing_type": "HDB"}
        is_valid, error = SegmentationService.validate_filters(filters)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_filters_invalid_housing(self):
        """Test filter validation with invalid housing type."""
        filters = {"housing_type": "INVALID"}
        is_valid, error = SegmentationService.validate_filters(filters)
        self.assertFalse(is_valid)
        self.assertIn("Invalid housing_type", error)

    def test_validate_filters_date_range(self):
        """Test filter validation with date range."""
        # Valid date range
        filters = {
            "date_from": datetime.now() - timedelta(days=30),
            "date_to": datetime.now(),
        }
        is_valid, error = SegmentationService.validate_filters(filters)
        self.assertTrue(is_valid)

    def test_validate_filters_invalid_date_range(self):
        """Test filter validation with invalid date range."""
        filters = {
            "date_from": datetime.now(),
            "date_to": datetime.now() - timedelta(days=30),
        }
        is_valid, error = SegmentationService.validate_filters(filters)
        self.assertFalse(is_valid)
        self.assertIn("date_from must be before date_to", error)

    def test_count_by_pdpa_status(self):
        """Test PDPA status counting."""
        counts = SegmentationService.count_by_pdpa_status(self.entity)

        self.assertEqual(counts["total"], 4)
        self.assertEqual(counts["opted_in"], 2)
        self.assertEqual(counts["opted_out"], 2)
        self.assertEqual(counts["opt_in_rate"], 50.0)

    def test_excluded_for_blast(self):
        """Test exclusion of non-consented customers for blast."""
        customer_ids = [
            self.customer_hdb.id,  # consented
            self.customer_landed.id,  # not consented
            self.customer_no_consent.id,  # not consented
        ]

        excluded = SegmentationService.get_excluded_for_blast(customer_ids)

        self.assertEqual(len(excluded), 2)
        self.assertIn(self.customer_landed.id, excluded)
        self.assertIn(self.customer_no_consent.id, excluded)
        self.assertNotIn(self.customer_hdb.id, excluded)


class TestSegmentationWithDateFilters(TestCase):
    """Test segmentation with date range filters."""

    def setUp(self):
        """Set up test data with dates."""
        self.entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST", "slug": "test-entity"},
            id=uuid.uuid4(),
        )

        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email="test@example.com",
            password="testpass123",
            entity=self.entity,
            role="admin",
        )

        # Create customers at different times
        self.old_customer = Customer.objects.create(
            name="Old Customer",
            mobile="+6590000010",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )
        # Manually set created_at
        self.old_customer.created_at = datetime.now() - timedelta(days=60)
        self.old_customer.save()

        self.new_customer = Customer.objects.create(
            name="New Customer",
            mobile="+6590000011",
            pdpa_consent=True,
            entity=self.entity,
            created_by=self.user,
        )

    def test_segment_date_from(self):
        """Test date_from filter."""
        filters = {
            "date_from": datetime.now() - timedelta(days=30),
            "pdpa": True,
        }
        queryset = SegmentationService.build_segment(filters)

        # Should only return new customer
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, "New Customer")

    def test_segment_date_to(self):
        """Test date_to filter."""
        filters = {
            "date_to": datetime.now() - timedelta(days=30),
            "pdpa": True,
        }
        queryset = SegmentationService.build_segment(filters)

        # Should only return old customer
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, "Old Customer")

    def test_segment_date_range(self):
        """Test date range filter."""
        filters = {
            "date_from": datetime.now() - timedelta(days=90),
            "date_to": datetime.now() - timedelta(days=30),
            "pdpa": True,
        }
        queryset = SegmentationService.build_segment(filters)

        # Should only return old customer
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().name, "Old Customer")
