"""Agreement Service — Phase 5: Sales Agreements & AVS Tracking."""

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.models import AuditLog, Entity, User
from apps.operations.models import Dog

from ..models import (
    AgreementLineItem,
    AgreementStatus,
    AgreementType,
    HousingType,
    SalesAgreement,
    TCTemplate,
)

logger = logging.getLogger(__name__)

# Large breeds that may have HDB restrictions
LARGE_BREEDS = [
    "Golden Retriever",
    "Labrador Retriever",
    "German Shepherd",
    "Rottweiler",
    "Doberman",
    "Chow Chow",
    "Husky",
    "Malamute",
    "Saint Bernard",
    "Great Dane",
    "Mastiff",
    "Bernese Mountain Dog",
]


class AgreementService:
    """Service for managing sales agreements."""

    # =============================================================================
    # GST Calculation (Deterministic per v1.1)
    # =============================================================================

    @staticmethod
    def extract_gst(price: Decimal, entity: Entity) -> Decimal:
        """
        Extract GST component from price using Singapore GST formula.

        Formula: price * gst_rate / (100 + gst_rate), rounded to 2 decimals (HALF_UP)
        Uses entity.gst_rate field (0.00 for exempt, 0.09 for standard 9% GST).

        Args:
            price: Total price including GST
            entity: Entity for GST determination

        Returns:
            GST component amount
        """
        # Use gst_rate field from entity (0.00 for exempt, 0.09 for standard)
        # Check for None explicitly since Decimal("0.00") is falsy
        gst_rate = entity.gst_rate if entity.gst_rate is not None else Decimal("0.09")
        
        # If GST rate is 0, return 0
        if gst_rate == Decimal("0.00"):
            return Decimal("0.00")

        # GST = price * gst_rate / (1 + gst_rate)
        # For example: 109 * 0.09 / 1.09 = 9.00
        divisor = Decimal("1") + gst_rate
        gst = price * gst_rate / divisor
        
        return gst.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_gst(price: Decimal, entity: Entity) -> tuple[Decimal, Decimal]:
        """
        Calculate price without GST and GST component.

        Returns:
            Tuple of (price_excl_gst, gst_component)
        """
        gst = AgreementService.extract_gst(price, entity)
        price_excl = price - gst

        return price_excl, gst

    # =============================================================================
    # State Machine
    # =============================================================================

    @staticmethod
    def can_transition(agreement: SalesAgreement, new_status: str) -> bool:
        """
        Check if status transition is valid.

        Valid transitions:
        - DRAFT → SIGNED (requires signatures)
        - DRAFT → CANCELLED
        - SIGNED → COMPLETED (requires AVS completion or rehoming)
        - SIGNED → CANCELLED
        """
        current = agreement.status

        valid_transitions = {
            AgreementStatus.DRAFT: [
                AgreementStatus.SIGNED,
                AgreementStatus.CANCELLED,
            ],
            AgreementStatus.SIGNED: [
                AgreementStatus.COMPLETED,
                AgreementStatus.CANCELLED,
            ],
            AgreementStatus.COMPLETED: [],
            AgreementStatus.CANCELLED: [],
        }

        return new_status in valid_transitions.get(current, [])

    @staticmethod
    def transition(
        agreement: SalesAgreement,
        new_status: str,
        user: User,
        reason: Optional[str] = None,
    ) -> SalesAgreement:
        """
        Transition agreement to new status with validation.

        Args:
            agreement: Agreement to transition
            new_status: Target status
            user: User making the transition
            reason: Optional reason for cancellation

        Returns:
            Updated agreement
        """
        if not AgreementService.can_transition(agreement, new_status):
            raise ValidationError(
                f"Invalid transition from {agreement.status} to {new_status}"
            )

        old_status = agreement.status
        agreement.status = new_status

        if new_status == AgreementStatus.SIGNED:
            from django.utils import timezone
            agreement.signed_at = timezone.now()

        agreement.save(update_fields=["status", "signed_at", "updated_at"])

        # Audit log
        AuditLog.objects.create(
            actor=user,
            action=AuditLog.Action.UPDATE,
            resource_type="SalesAgreement",
            resource_id=str(agreement.id),
            payload={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
            },
        )

        logger.info(
            f"Agreement {agreement.id} transitioned: {old_status} → {new_status} by {user.email}"
        )

        return agreement

    # =============================================================================
    # Agreement Creation
    # =============================================================================

    @staticmethod
    def create_agreement(
        type: str,
        entity_id: UUID,
        dog_ids: list[UUID],
        buyer_info: dict,
        pricing: dict,
        created_by: User,
        special_conditions: str = "",
        pdpa_consent: bool = False,
    ) -> SalesAgreement:
        """
        Create a new sales agreement.

        Args:
            type: Agreement type (B2C, B2B, REHOME)
            entity_id: Entity ID
            dog_ids: List of dog IDs to include
            buyer_info: Dict with buyer details
            pricing: Dict with total_amount, deposit, payment_method
            created_by: User creating the agreement
            special_conditions: Optional special conditions
            pdpa_consent: PDPA consent flag

        Returns:
            Created SalesAgreement
        """
        # Validate entity
        try:
            entity = Entity.objects.get(id=entity_id)
        except Entity.DoesNotExist:
            raise ValidationError("Entity not found")

        # Validate dogs
        dogs = Dog.objects.filter(id__in=dog_ids, entity_id=entity_id)
        if len(dogs) != len(dog_ids):
            raise ValidationError("One or more dogs not found or not in entity")

        # Validate PDPA consent
        if not pdpa_consent:
            raise ValidationError("PDPA consent is required")

        # Calculate GST
        total_amount = Decimal(str(pricing.get("total_amount", 0)))
        gst_component = AgreementService.extract_gst(total_amount, entity)

        deposit = Decimal(str(pricing.get("deposit", 0)))
        balance = total_amount - deposit

        # Create agreement
        with transaction.atomic():
            agreement = SalesAgreement.objects.create(
                type=type,
                entity=entity,
                buyer_name=buyer_info["name"],
                buyer_nric=buyer_info.get("nric", ""),
                buyer_mobile=buyer_info["mobile"],
                buyer_email=buyer_info["email"],
                buyer_address=buyer_info["address"],
                buyer_housing_type=buyer_info.get("housing_type", HousingType.OTHER),
                pdpa_consent=pdpa_consent,
                total_amount=total_amount,
                gst_component=gst_component,
                deposit=deposit,
                balance=balance,
                payment_method=pricing.get("payment_method", "CASH"),
                special_conditions=special_conditions,
                created_by=created_by,
                status=AgreementStatus.DRAFT,
            )

            # Create line items
            for i, dog in enumerate(dogs):
                # For B2B, each dog may have individual pricing
                # For B2C/REHOME, split total proportionally or use individual prices
                AgreementLineItem.objects.create(
                    agreement=agreement,
                    dog=dog,
                    price=total_amount / len(dogs),  # Split equally for now
                    gst_component=gst_component / len(dogs),
                )

            # Audit log
            AuditLog.objects.create(
                actor=created_by,
                action=AuditLog.Action.CREATE,
                resource_type="SalesAgreement",
                resource_id=str(agreement.id),
                payload={
                    "type": type,
                    "entity": entity.name,
                    "dogs": [str(d.id) for d in dogs],
                    "total": str(total_amount),
                },
            )

        logger.info(f"Agreement {agreement.id} created by {created_by.email}")

        return agreement

    @staticmethod
    def update_agreement(
        agreement: SalesAgreement,
        user: User,
        buyer_info: Optional[dict] = None,
        pricing: Optional[dict] = None,
        special_conditions: Optional[str] = None,
        pdpa_consent: Optional[bool] = None,
    ) -> SalesAgreement:
        """
        Update a draft agreement.

        Only draft agreements can be updated.
        """
        if agreement.status != AgreementStatus.DRAFT:
            raise ValidationError("Only draft agreements can be updated")

        updates = {}

        if buyer_info:
            if "name" in buyer_info:
                agreement.buyer_name = buyer_info["name"]
            if "nric" in buyer_info:
                agreement.buyer_nric = buyer_info["nric"]
            if "mobile" in buyer_info:
                agreement.buyer_mobile = buyer_info["mobile"]
            if "email" in buyer_info:
                agreement.buyer_email = buyer_info["email"]
            if "address" in buyer_info:
                agreement.buyer_address = buyer_info["address"]
            if "housing_type" in buyer_info:
                agreement.buyer_housing_type = buyer_info["housing_type"]
            updates["buyer_info"] = buyer_info

        if pricing:
            if "total_amount" in pricing:
                agreement.total_amount = Decimal(str(pricing["total_amount"]))
                agreement.gst_component = AgreementService.extract_gst(
                    agreement.total_amount, agreement.entity
                )
            if "deposit" in pricing:
                agreement.deposit = Decimal(str(pricing["deposit"]))
                agreement.balance = agreement.total_amount - agreement.deposit
            if "payment_method" in pricing:
                agreement.payment_method = pricing["payment_method"]
            updates["pricing"] = pricing

        if special_conditions is not None:
            agreement.special_conditions = special_conditions
            updates["special_conditions"] = special_conditions

        if pdpa_consent is not None:
            agreement.pdpa_consent = pdpa_consent
            updates["pdpa_consent"] = pdpa_consent

        agreement.save()

        # Audit log
        if updates:
            AuditLog.objects.create(
                actor=user,
                action=AuditLog.Action.UPDATE,
                resource_type="SalesAgreement",
                resource_id=str(agreement.id),
                payload=updates,
            )

        logger.info(f"Agreement {agreement.id} updated by {user.email}")

        return agreement

    # =============================================================================
    # HDB Warning
    # =============================================================================

    @staticmethod
    def check_hdb_warning(agreement: SalesAgreement) -> Optional[dict]:
        """
        Check if HDB warning should be shown.

        Returns warning dict if buyer has HDB housing and dogs include large breeds.
        """
        if agreement.buyer_housing_type != HousingType.HDB:
            return None

        large_breeds_in_agreement = []
        for item in agreement.line_items.all():
            if item.dog.breed in LARGE_BREEDS:
                large_breeds_in_agreement.append(item.dog.name)

        if not large_breeds_in_agreement:
            return None

        return {
            "warning": True,
            "message": (
                "HDB ALERT: The selected dog(s) may exceed HDB size restrictions. "
                "Please verify with HDB before proceeding."
            ),
            "breeds": large_breeds_in_agreement,
        }

    # =============================================================================
    # T&C Templates
    # =============================================================================

    @staticmethod
    def get_tc_content(type: str) -> str:
        """
        Get T&C content for agreement type.

        Returns default content if no template exists.
        """
        try:
            template = TCTemplate.objects.get(type=type)
            return template.content
        except TCTemplate.DoesNotExist:
            return AgreementService._default_tc_content(type)

    @staticmethod
    def _default_tc_content(type: str) -> str:
        """Default T&C content by type."""
        templates = {
            AgreementType.B2C: """
TERMS & CONDITIONS - B2C SALE

1. Deposit: The deposit paid is NON-REFUNDABLE except in case of breach by seller.
2. Health Guarantee: Dog is sold in good health as examined by licensed veterinarian.
3. Transfer: Ownership transfer will be processed via AVS upon full payment.
4. Returns: No returns accepted after 14 days from collection date.
5. PDPA: Buyer consents to data collection per PDPA.
""",
            AgreementType.B2B: """
TERMS & CONDITIONS - B2B SALE

1. Commercial Terms: Payment terms NET 30 days unless otherwise agreed.
2. Health Certificate: Health certificate provided per AVS requirements.
3. Transfer: Ownership transfer within 7 business days of payment.
4. Liability: Limited to purchase price; excludes consequential damages.
5. Governing Law: Singapore law applies.
""",
            AgreementType.REHOME: """
TERMS & CONDITIONS - REHOMING

1. No Purchase Price: This is a rehoming arrangement at $0.
2. Care Requirements: New owner agrees to proper care and welfare.
3. AVS Transfer: Transfer of ownership required within 14 days.
4. Follow-up: Original owner may request welfare updates for 6 months.
5. Return Policy: Dog may be returned if care standards not met.
""",
        }
        return templates.get(type, "Terms and conditions apply.")

    @staticmethod
    def update_tc_template(
        type: str,
        content: str,
        updated_by: User,
    ) -> TCTemplate:
        """Update or create T&C template."""
        template, created = TCTemplate.objects.update_or_create(
            type=type,
            defaults={
                "content": content,
                "updated_by": updated_by,
            },
        )

        if not created:
            template.version += 1
            template.save(update_fields=["version", "updated_by", "updated_at"])

        logger.info(f"T&C template for {type} updated by {updated_by.email}")

        return template

    # =============================================================================
    # Agreement Actions
    # =============================================================================

    @staticmethod
    def sign_agreement(
        agreement_id: UUID,
        signed_by: User,
        signature_data: str,
        ip_address: str,
        user_agent: str,
    ) -> bool:
        """
        Sign an agreement and transition to SIGNED state.

        Args:
            agreement_id: Agreement UUID
            signed_by: User signing the agreement
            signature_data: Signature image/data (base64)
            ip_address: IP address of signer
            user_agent: User agent of signer

        Returns:
            True if signed successfully
        """
        try:
            agreement = SalesAgreement.objects.get(id=agreement_id)
        except SalesAgreement.DoesNotExist:
            return False

        # Check if can transition to SIGNED
        if not AgreementService.can_transition(agreement, AgreementStatus.SIGNED):
            return False

        from django.utils import timezone
        from ..models import Signature

        with transaction.atomic():
            # Create signature record
            Signature.objects.create(
                agreement=agreement,
                signed_by=signed_by,
                signature_data=signature_data,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=timezone.now(),
            )

            # Transition to SIGNED
            AgreementService.transition(
                agreement=agreement,
                new_status=AgreementStatus.SIGNED,
                user=signed_by,
            )

        return True

    @staticmethod
    def complete_agreement(
        agreement_id: UUID,
        completed_by: User,
    ) -> bool:
        """
        Complete an agreement and transition to COMPLETED state.

        Args:
            agreement_id: Agreement UUID
            completed_by: User completing the agreement

        Returns:
            True if completed successfully
        """
        try:
            agreement = SalesAgreement.objects.get(id=agreement_id)
        except SalesAgreement.DoesNotExist:
            return False

        # Check if can transition to COMPLETED
        if not AgreementService.can_transition(agreement, AgreementStatus.COMPLETED):
            return False

        from django.utils import timezone

        with transaction.atomic():
            agreement.status = AgreementStatus.COMPLETED
            agreement.completed_at = timezone.now()
            agreement.save(update_fields=["status", "completed_at", "updated_at"])

            # Audit log
            AuditLog.objects.create(
                actor=completed_by,
                action=AuditLog.Action.UPDATE,
                resource_type="SalesAgreement",
                resource_id=str(agreement_id),
                payload={
                    "old_status": AgreementStatus.SIGNED,
                    "new_status": AgreementStatus.COMPLETED,
                },
            )

        logger.info(f"Agreement {agreement_id} completed by {completed_by.email}")
        return True

    @staticmethod
    def cancel_agreement(
        agreement_id: UUID,
        cancelled_by: User,
        reason: str = "",
    ) -> bool:
        """
        Cancel an agreement and transition to CANCELLED state.

        Args:
            agreement_id: Agreement UUID
            cancelled_by: User cancelling the agreement
            reason: Optional cancellation reason

        Returns:
            True if cancelled successfully
        """
        try:
            agreement = SalesAgreement.objects.get(id=agreement_id)
        except SalesAgreement.DoesNotExist:
            return False

        # Check if can transition to CANCELLED
        if not AgreementService.can_transition(agreement, AgreementStatus.CANCELLED):
            return False

        from django.utils import timezone

        # Capture state BEFORE mutation for correct audit trail
        old_status = agreement.status

        with transaction.atomic():
            agreement.status = AgreementStatus.CANCELLED
            agreement.cancelled_at = timezone.now()
            agreement.save(update_fields=["status", "cancelled_at", "updated_at"])

            # Audit log
            AuditLog.objects.create(
                actor=cancelled_by,
                action=AuditLog.Action.UPDATE,
                resource_type="SalesAgreement",
                resource_id=str(agreement_id),
                payload={
                    "old_status": old_status,
                    "new_status": AgreementStatus.CANCELLED,
                    "reason": reason,
                },
            )

        logger.info(f"Agreement {agreement_id} cancelled by {cancelled_by.email}: {reason}")
        return True

    @staticmethod
    def calculate_totals(agreement: SalesAgreement) -> dict:
        """
        Calculate agreement totals from line items.

        Args:
            agreement: SalesAgreement instance

        Returns:
            Dict with subtotal, gst_amount, total
        """
        from decimal import Decimal

        subtotal = Decimal("0.00")
        gst_amount = Decimal("0.00")

        for item in agreement.line_items.all():
            subtotal += item.line_total
            gst_amount += item.gst_amount

        total = subtotal + gst_amount

        return {
            "subtotal": subtotal,
            "gst_amount": gst_amount,
            "total": total,
        }
