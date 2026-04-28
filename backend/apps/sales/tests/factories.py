"""Sales & AVS Test Factories
===================================
Phase 5: Sales Agreements & AVS Tracking

Factory Boy factories for sales models.
"""

import uuid
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.core.models import Entity, User
from apps.sales.models import (
    AgreementLineItem,
    AgreementStatus,
    AgreementType,
    AVSStatus,
    AVSTransfer,
    SalesAgreement,
    Signature,
    TCTemplate,
)


class SalesAgreementFactory(DjangoModelFactory):
    """Factory for SalesAgreement model."""

    class Meta:
        model = SalesAgreement

    type = factory.Iterator([AgreementType.B2C, AgreementType.B2B, AgreementType.REHOME])
    status = AgreementStatus.DRAFT
    buyer_name = factory.Faker("name")
    buyer_mobile = factory.Faker("phone_number")
    buyer_email = factory.Faker("email")
    buyer_address = factory.Faker("address")
    total_amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    gst_component = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    deposit = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    balance = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)

    @factory.lazy_attribute
    def entity(self):
        entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST"},
            id=uuid.uuid4(),
        )
        return entity

    @factory.lazy_attribute
    def created_by(self):
        return User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password="testpass123",
            entity=self.entity,
            role="admin",
        )


class AgreementLineItemFactory(DjangoModelFactory):
    """Factory for AgreementLineItem model."""

    class Meta:
        model = AgreementLineItem

    description = factory.Faker("sentence", nb_words=5)
    quantity = 1
    unit_price = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)

    @factory.lazy_attribute
    def agreement(self):
        return SalesAgreementFactory()

    @factory.lazy_attribute
    def line_total(self):
        return self.unit_price * self.quantity

    @factory.lazy_attribute
    def gst_amount(self):
        return self.line_total * Decimal("0.09")


class TCTemplateFactory(DjangoModelFactory):
    """Factory for TCTemplate model."""

    class Meta:
        model = TCTemplate

    name = factory.Faker("catch_phrase")
    template_html = factory.Faker("text", max_nb_chars=2000)
    version = factory.Faker("random_number", digits=1)
    is_active = True

    @factory.lazy_attribute
    def entity(self):
        from apps.core.models import Entity
        entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST"},
            id=factory.Faker("uuid4").generate(),
        )
        return entity


class SignatureFactory(DjangoModelFactory):
    """Factory for Signature model."""

    class Meta:
        model = Signature

    signature_data = factory.Faker("text", max_nb_chars=500)
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")

    @factory.lazy_attribute
    def agreement(self):
        from apps.core.models import User
        from apps.sales.models import SalesAgreement
        entity, _ = Entity.objects.get_or_create(
            defaults={"name": "Test Entity", "code": "TEST"},
            id=factory.Faker("uuid4").generate(),
        )
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            entity=entity,
            role="admin",
        )
        return SalesAgreement.objects.create(
            entity=entity,
            created_by=user,
            agreement_type=AgreementType.B2C,
            status=AgreementStatus.SIGNED,
            buyer_name="Test Buyer",
            buyer_mobile="+6591234567",
            buyer_email="buyer@example.com",
            subtotal=1000.00,
            gst_amount=82.57,
            total=1082.57,
            terms_version="1.0",
        )

    @factory.lazy_attribute
    def signed_by(self):
        from apps.core.models import User
        from apps.sales.models import SalesAgreement
        agreement = self.agreement
        return agreement.created_by
