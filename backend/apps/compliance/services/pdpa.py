"""PDPA Service
==============
Phase 6: Compliance & NParks Reporting

PDPA consent enforcement and audit logging.
Deterministic - zero AI logic.

Features:
- Hard PDPA filters at query level
- Immutable consent audit log
- Blast eligibility checking
- No override path: consent=False always excluded
"""

import logging
from typing import Optional, Tuple
from uuid import UUID

from django.db.models import QuerySet
from django.db import transaction

from apps.core.models import User

from ..models import PDPAConsentLog, PDPAAction
from ..schemas import PDPAConsentCheckResponse

logger = logging.getLogger(__name__)


class PDPAService:
    """Service for PDPA compliance and consent management."""

    @staticmethod
    def filter_consent(queryset: QuerySet) -> QuerySet:
        """
        Hard filter for PDPA consent.

        Applies WHERE pdpa_consent=True at query level.
        No exceptions, no override path.

        Args:
            queryset: QuerySet to filter

        Returns:
            Filtered QuerySet with only PDPA-consented records
        """
        return queryset.filter(pdpa_consent=True)

    @staticmethod
    def log_consent_change(
        customer_id: UUID,
        action: str,
        previous_state: bool,
        new_state: bool,
        actor: User,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> PDPAConsentLog:
        """
        Log PDPA consent change to immutable audit trail.

        Creates append-only log entry. Cannot be updated or deleted.

        Args:
            customer_id: Customer UUID
            action: "OPT_IN" or "OPT_OUT"
            previous_state: Previous consent state
            new_state: New consent state
            actor: User making the change
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created PDPAConsentLog entry
        """
        with transaction.atomic():
            log = PDPAConsentLog.objects.create(
                customer_id=customer_id,
                action=action,
                previous_state=previous_state,
                new_state=new_state,
                actor=actor,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        logger.info(
            f"PDPA consent logged: customer={customer_id}, "
            f"action={action}, actor={actor.email}"
        )

        return log

    @staticmethod
    def check_blast_eligibility(customer_ids: list[UUID]) -> PDPAConsentCheckResponse:
        """
        Check blast eligibility for customer list.

        Splits customers into eligible and excluded based on PDPA consent.

        Args:
            customer_ids: List of customer UUIDs to check

        Returns:
            PDPAConsentCheckResponse with eligible/excluded split
        """
        from apps.customers.models import Customer

        customers = Customer.objects.filter(id__in=customer_ids)
        eligible_ids = [c.id for c in customers if c.pdpa_consent]
        excluded_ids = [c.id for c in customers if not c.pdpa_consent]

        logger.info(
            "PDPA blast eligibility: %d eligible, %d excluded of %d total",
            len(eligible_ids), len(excluded_ids), len(customer_ids),
        )

        return PDPAConsentCheckResponse(
            eligible_ids=eligible_ids,
            excluded_ids=excluded_ids,
            eligible_count=len(eligible_ids),
            excluded_count=len(excluded_ids),
            exclusion_reason="PDPA consent not given" if excluded_ids else "",
        )

    @staticmethod
    def is_consented(customer_id: UUID) -> bool:
        """
        Check if customer has PDPA consent.

        Args:
            customer_id: Customer UUID

        Returns:
            True if customer has opted in to PDPA, False otherwise
        """
        from apps.customers.models import Customer

        try:
            return Customer.objects.get(id=customer_id).pdpa_consent
        except Customer.DoesNotExist:
            return False

    @staticmethod
    def get_consent_log(customer_id: UUID, limit: int = 50) -> list[PDPAConsentLog]:
        """
        Get PDPA consent history for customer.

        Args:
            customer_id: Customer UUID
            limit: Maximum number of entries to return

        Returns:
            List of PDPAConsentLog entries
        """
        return list(
            PDPAConsentLog.objects.filter(customer_id=customer_id)
            .order_by("-created_at")
            [:limit]
        )

    @staticmethod
    def validate_consent_change(
        customer_id: UUID,
        new_state: bool,
        actor: User,
    ) -> Tuple[bool, str]:
        """
        Validate PDPA consent change.

        Checks for duplicate changes or invalid state transitions.

        Args:
            customer_id: Customer UUID
            new_state: Desired new consent state
            actor: User making the change

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get latest consent log
        latest = (
            PDPAConsentLog.objects.filter(customer_id=customer_id)
            .order_by("-created_at")
            .first()
        )

        if latest:
            current_state = latest.new_state

            # Check for duplicate
            if current_state == new_state:
                return (
                    False,
                    f"Customer already has consent={new_state}. No change needed.",
                )

        return True, ""

    @staticmethod
    def get_latest_consent_state(customer_id: UUID) -> Optional[bool]:
        """
        Get customer's latest PDPA consent state.

        Args:
            customer_id: Customer UUID

        Returns:
            Current consent state (True/False) or None if no history
        """
        latest = (
            PDPAConsentLog.objects.filter(customer_id=customer_id)
            .order_by("-created_at")
            .first()
        )

        return latest.new_state if latest else None

    @staticmethod
    def count_consented_customers(entity_id: UUID) -> int:
        """
        Count customers with PDPA consent for entity.

        Args:
            entity_id: Entity UUID

        Returns:
            Number of consented customers
        """
        from apps.customers.models import Customer
        return Customer.objects.filter(
            entity_id=entity_id,
            pdpa_consent=True,
        ).count()

    @staticmethod
    def count_opted_out_customers(entity_id: UUID) -> int:
        """
        Count customers opted out of PDPA for entity.

        Args:
            entity_id: Entity UUID

        Returns:
            Number of opted-out customers
        """
        from apps.customers.models import Customer
        return Customer.objects.filter(
            entity_id=entity_id,
            pdpa_consent=False,
        ).count()
