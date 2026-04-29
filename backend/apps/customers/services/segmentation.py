"""Segmentation Service
======================
Phase 7: Customer DB & Marketing Blast

Customer segmentation with composable filters and PDPA enforcement.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from django.db.models import Q, QuerySet
from django.core.cache import cache

from apps.core.models import Entity
from ..models import Customer, Segment

logger = logging.getLogger(__name__)


class SegmentationService:
    """Service for building customer segments."""

    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    def build_segment(filters: dict, entity_scope: Optional[Entity] = None) -> QuerySet:
        """
        Build customer segment from filter criteria.

        Automatically applies PDPA hard filter at query level.

        Args:
            filters: Dict with keys: breed, entity_id, pdpa, date_from, date_to, housing_type
            entity_scope: Optional entity to scope results to

        Returns:
            QuerySet of matching customers
        """
        queryset = Customer.objects.all()

        # Entity scoping
        if entity_scope:
            queryset = queryset.filter(entity=entity_scope)
        elif filters.get("entity_id"):
            queryset = queryset.filter(entity_id=filters["entity_id"])

        # HARD FILTER: PDPA consent required for marketing
        # Default to True (only consented customers)
        pdpa_required = filters.get("pdpa", True)
        if pdpa_required:
            queryset = queryset.filter(pdpa_consent=True)

        # Housing type filter
        if filters.get("housing_type"):
            queryset = queryset.filter(housing_type=filters["housing_type"])

        # Date range filter
        if filters.get("date_from"):
            queryset = queryset.filter(created_at__gte=filters["date_from"])

        if filters.get("date_to"):
            queryset = queryset.filter(created_at__lte=filters["date_to"])

        # Note: Breed filter would require join with SalesAgreement/LineItem
        # For now, document as placeholder - would need additional model relationships
        if filters.get("breed"):
            # Placeholder: Would filter by dogs purchased
            logger.info(f"Breed filter requested: {filters['breed']} (placeholder)")
            pass

        return queryset

    @staticmethod
    def preview_segment(filters: dict, entity_scope: Optional[Entity] = None) -> int:
        """
        Preview segment count without fetching data.

        Args:
            filters: Segment filter criteria
            entity_scope: Optional entity scope

        Returns:
            Count of matching customers
        """
        cache_key = SegmentationService._get_cache_key(filters, entity_scope)
        cached = cache.get(cache_key)

        if cached is not None:
            logger.debug(f"Segment cache hit: {cache_key}")
            return cached

        queryset = SegmentationService.build_segment(filters, entity_scope)
        count = queryset.count()

        cache.set(cache_key, count, SegmentationService.CACHE_TTL)
        logger.debug(f"Segment cache set: {cache_key} = {count}")

        return count

    @staticmethod
    def get_segment_customers(segment_id: UUID) -> QuerySet:
        """
        Get customers matching a saved segment.

        Args:
            segment_id: Segment UUID

        Returns:
            QuerySet of matching customers
        """
        try:
            segment = Segment.objects.get(id=segment_id)
        except Segment.DoesNotExist:
            return Customer.objects.none()

        queryset = SegmentationService.build_segment(
            segment.filters_json,
            entity_scope=segment.entity,
        )

        return queryset

    @staticmethod
    def build_composable_filters(filters: dict) -> Q:
        """
        Build composable Q objects for complex queries.

        Args:
            filters: Filter criteria

        Returns:
            Q object combining filters
        """
        q_objects = Q()

        # Always require PDPA consent for marketing
        if filters.get("pdpa", True):
            q_objects &= Q(pdpa_consent=True)

        if filters.get("housing_type"):
            q_objects &= Q(housing_type=filters["housing_type"])

        if filters.get("date_from"):
            q_objects &= Q(created_at__gte=filters["date_from"])

        if filters.get("date_to"):
            q_objects &= Q(created_at__lte=filters["date_to"])

        return q_objects

    @staticmethod
    def invalidate_cache(filters: dict, entity_scope: Optional[Entity] = None):
        """
        Invalidate cached segment count.

        Args:
            filters: Segment filter criteria
            entity_scope: Optional entity scope
        """
        cache_key = SegmentationService._get_cache_key(filters, entity_scope)
        cache.delete(cache_key)
        logger.debug(f"Segment cache invalidated: {cache_key}")

    @staticmethod
    def _get_cache_key(filters: dict, entity_scope: Optional[Entity] = None) -> str:
        """
        Generate cache key for segment.

        Args:
            filters: Filter criteria
            entity_scope: Entity scope

        Returns:
            Cache key string
        """
        filters_str = json.dumps(filters, sort_keys=True, default=str)
        entity_id = str(entity_scope.id) if entity_scope else "all"
        return f"segment_count:{entity_id}:{hash(filters_str)}"

    @staticmethod
    def validate_filters(filters: dict) -> tuple[bool, str]:
        """
        Validate segment filters.

        Args:
            filters: Filter criteria to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_housing = ["HDB", "CONDO", "LANDED", "OTHER"]

        if filters.get("housing_type") and filters["housing_type"] not in valid_housing:
            return False, f"Invalid housing_type. Must be one of: {valid_housing}"

        date_from = filters.get("date_from")
        date_to = filters.get("date_to")

        if date_from and date_to:
            if isinstance(date_from, str):
                try:
                    date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                    date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                except ValueError:
                    return False, "Invalid date format"

            if date_from > date_to:
                return False, "date_from must be before date_to"

        return True, ""

    @staticmethod
    def get_available_filters() -> dict:
        """
        Get available filter options.

        Returns:
            Dict with available filter values
        """
        return {
            "housing_types": ["HDB", "CONDO", "LANDED", "OTHER"],
            "entities": list(Entity.objects.values_list("code", "name")),
            "breeds": []  # Would populate from Dog model
        }

    @staticmethod
    def count_by_pdpa_status(entity_scope: Optional[Entity] = None) -> dict:
        """
        Get customer counts by PDPA consent status.

        Args:
            entity_scope: Optional entity scope

        Returns:
            Dict with counts: total, opted_in, opted_out
        """
        queryset = Customer.objects.all()

        if entity_scope:
            queryset = queryset.filter(entity=entity_scope)

        total = queryset.count()
        opted_in = queryset.filter(pdpa_consent=True).count()
        opted_out = total - opted_in

        return {
            "total": total,
            "opted_in": opted_in,
            "opted_out": opted_out,
            "opt_in_rate": round(opted_in / total * 100, 1) if total else 0,
        }

    @staticmethod
    def get_excluded_for_blast(customer_ids: list[UUID]) -> list[UUID]:
        """
        Get list of customers excluded from blast (PDPA opt-out).

        Args:
            customer_ids: List of customer UUIDs to check

        Returns:
            List of excluded customer IDs
        """
        excluded = Customer.objects.filter(
            id__in=customer_ids,
            pdpa_consent=False,
        ).values_list("id", flat=True)

        return list(excluded)
