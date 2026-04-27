"""
Breeding & Genetics Test Factories
===================================
Phase 4: Breeding & Genetics Engine

Factory Boy factories for breeding models.
"""

import factory
from factory.django import DjangoModelFactory

from apps.breeding.models import (
    BreedingRecord,
    DogClosure,
    Litter,
    MateCheckOverride,
    Puppy,
)
from apps.core.models import Entity
from apps.operations.models import Dog


class BreedingRecordFactory(DjangoModelFactory):
    """Factory for BreedingRecord model."""

    class Meta:
        model = BreedingRecord

    dam = factory.SubFactory(
        "apps.operations.tests.factories.DogFactory",
        gender="F"
    )
    sire1 = factory.SubFactory(
        "apps.operations.tests.factories.DogFactory",
        gender="M"
    )
    sire2 = None
    date = factory.Faker("date_this_year")
    method = BreedingRecord.Method.NATURAL
    confirmed_sire = BreedingRecord.ConfirmedSire.UNCONFIRMED
    notes = factory.Faker("text", max_nb_chars=200)

    @factory.lazy_attribute
    def entity(self):
        return self.dam.entity


class LitterFactory(DjangoModelFactory):
    """Factory for Litter model."""

    class Meta:
        model = Litter

    breeding_record = factory.SubFactory(BreedingRecordFactory)
    whelp_date = factory.Faker("date_this_year")
    delivery_method = Litter.DeliveryMethod.NATURAL
    alive_count = factory.Faker("random_int", min=1, max=8)
    stillborn_count = factory.Faker("random_int", min=0, max=2)
    notes = factory.Faker("text", max_nb_chars=200)

    @factory.lazy_attribute
    def entity(self):
        return self.breeding_record.entity


class PuppyFactory(DjangoModelFactory):
    """Factory for Puppy model."""

    class Meta:
        model = Puppy

    litter = factory.SubFactory(LitterFactory)
    microchip = factory.Faker("random_int", min=100000000, max=999999999)
    gender = factory.Iterator(["M", "F"])
    colour = factory.Faker("color_name")
    birth_weight = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    confirmed_sire = BreedingRecord.ConfirmedSire.UNCONFIRMED
    paternity_method = Puppy.PaternityMethod.UNCONFIRMED
    status = Puppy.Status.ALIVE

    @factory.lazy_attribute
    def entity(self):
        return self.litter.entity


class DogClosureFactory(DjangoModelFactory):
    """Factory for DogClosure model."""

    class Meta:
        model = DogClosure

    ancestor = factory.SubFactory("apps.operations.tests.factories.DogFactory")
    descendant = factory.SubFactory("apps.operations.tests.factories.DogFactory")
    depth = factory.Faker("random_int", min=1, max=5)

    @factory.lazy_attribute
    def entity(self):
        return self.ancestor.entity


class MateCheckOverrideFactory(DjangoModelFactory):
    """Factory for MateCheckOverride model."""

    class Meta:
        model = MateCheckOverride

    dam = factory.SubFactory(
        "apps.operations.tests.factories.DogFactory",
        gender="F"
    )
    sire1 = factory.SubFactory(
        "apps.operations.tests.factories.DogFactory",
        gender="M"
    )
    sire2 = None
    coi_pct = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    saturation_pct = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    verdict = factory.Iterator(["SAFE", "CAUTION", "HIGH_RISK"])
    override_reason = factory.Faker("sentence", nb_words=6)
    override_notes = factory.Faker("text", max_nb_chars=500)

    @factory.lazy_attribute
    def entity(self):
        return self.dam.entity
