"""Test SALES-003: create_agreement should verify entity access.

FIX-03: `require_entity_access(request)` is called bare in create_agreement.
Since `require_entity_access` is a decorator (returns wrapper function),
a bare call creates it but never executes it — zero access check runs.
A non-management user could create an agreement for any entity.
"""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from django.test import TestCase
from ninja.errors import HttpError


class TestCreateAgreementEntityAccess(TestCase):
    """Verify entity access check in create_agreement."""

    def test_non_management_blocked_from_other_entity(self):
        """Non-management user must NOT create agreements for other entities."""
        from apps.sales.routers.agreements import create_agreement
        from apps.sales.schemas import AgreementCreate
        # Arrange
        user_entity = uuid4()
        other_entity = uuid4()
        user = MagicMock()
        user.role = "SALES"
        user.entity_id = str(user_entity)
        mock_request = MagicMock()
        mock_request.user = user

        # Patch get_user_from_request to return our user
        with patch("apps.sales.routers.agreements.AuthenticationService.get_user_from_request", return_value=user):
            # Create valid AgreementCreate with full required data
            data = AgreementCreate(
                entity_id=other_entity,
                dog_ids=[uuid4()],
                type="B2C",
                buyer_info={
                    "name": "Test",
                    "nric": "T1234567A",
                    "mobile": "9123456789",
                    "email": "test@example.com",
                    "address": "123 Wellfond Street, Singapore 123456",
                    "housing_type": "HDB",
                },
                pricing={"total_amount": 1000, "deposit": 200, "payment_method": "T/T"},
                special_conditions="",
                pdpa_consent=False,
                tc_acceptance=False,
            )
            with pytest.raises(HttpError) as exc_info:
                create_agreement(mock_request, data)
            assert exc_info.value.status_code == 403

    def test_management_allowed_any_entity(self):
        """Management user CAN create agreements for any entity."""
        from apps.sales.routers.agreements import create_agreement
        from apps.sales.schemas import AgreementCreate
        # Arrange
        user_entity = uuid4()
        other_entity = uuid4()
        user = MagicMock()
        user.role = "MANAGEMENT"
        user.entity_id = str(user_entity)
        mock_request = MagicMock()
        mock_request.user = user

        # Patch get_user_from_request and the service to avoid full DB lifecycle
        with patch("apps.sales.routers.agreements.AuthenticationService.get_user_from_request", return_value=user):
            with patch("apps.sales.routers.agreements.AgreementService.create_agreement", return_value=MagicMock(entity_id=other_entity)):
                data = AgreementCreate(
                    entity_id=other_entity,
                    dog_ids=[uuid4()],
                    type="B2C",
                    buyer_info={
                        "name": "Test",
                        "nric": "T1234567A",
                        "mobile": "9123456789",
                        "email": "test@example.com",
                        "address": "123 Wellfond Street, Singapore 123456",
                        "housing_type": "HDB",
                    },
                    pricing={"total_amount": 1000, "deposit": 200, "payment_method": "T/T"},
                    special_conditions="",
                    pdpa_consent=False,
                    tc_acceptance=False,
                )
                create_agreement(mock_request, data)
