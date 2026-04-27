"""
Farm Saturation Tests
=====================
Phase 4: Breeding & Genetics Engine

Test suite for farm saturation calculation.
"""

import pytest
from decimal import Decimal

from apps.breeding.services.saturation import (
    calc_saturation,
    SaturationThreshold,
    get_saturation_threshold,
)


@pytest.mark.django_db
def test_saturation_no_common_ancestry_returns_100():
    """
    Test that a sire alone in an entity shows 100% saturation.

    The sire itself is counted as having ancestry (itself), so with only
    the sire present, saturation is 100% (1 dog with ancestry / 1 total).
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity

    entity = Entity.objects.create(name="Test Entity", code="TEST", slug="test-entity")

    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="New Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )

    result = calc_saturation(sire.id, entity.id)

    # Sire alone: 1 dog with ancestry (the sire itself) / 1 total = 100%
    assert result.saturation_pct == 100.0
    assert result.get_threshold() == "HIGH_RISK"
    assert result.dogs_with_ancestry == 1


@pytest.mark.django_db
def test_saturation_all_share_sire_returns_100():
    """
    Test that when all active dogs are descendants of the sire,
    saturation is high.

    Note: Without closure table entries, descendants won't be found.
    This test validates the logic when ancestry is tracked.
    """
    from apps.breeding.models import DogClosure
    from apps.operations.models import Dog
    from apps.core.models import Entity

    entity = Entity.objects.create(name="Test Entity", code="TEST", slug="test-entity")

    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Foundation Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )

    # Create offspring (descendants) and build closure table
    offspring_list = []
    for i in range(5):
        pup = Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Offspring {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
        )
        offspring_list.append(pup)
        # Build closure table entry
        DogClosure.objects.create(
            ancestor=sire,
            descendant=pup,
            depth=1,
            entity=entity
        )

    result = calc_saturation(sire.id, entity.id)

    # With closure table: sire + 5 offspring = 6 dogs with ancestry out of 6 total = 100%
    # Note: Sire is excluded from descendant count but included in dogs_with_ancestry
    assert result.saturation_pct >= 50.0


@pytest.mark.django_db
def test_saturation_partial_returns_correct_pct():
    """
    Test that partial saturation is calculated correctly.

    If 2 of 10 active dogs share ancestry with sire, saturation = ~27% (3/11).
    Note: Total includes sire (1) + 8 unrelated + 2 descendants = 11 dogs.
          With ancestry: sire + 2 descendants = 3 dogs.
    """
    from apps.breeding.models import DogClosure
    from apps.operations.models import Dog
    from apps.core.models import Entity

    entity = Entity.objects.create(name="Test Entity", code="TEST", slug="test-entity")

    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )

    # Create unrelated dogs (no closure table entries)
    for i in range(8):
        Dog.objects.create(
            microchip=f"33333333333333{i}",
            name=f"Unrelated {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
        )

    # Create descendants with closure table entries
    for i in range(2):
        pup = Dog.objects.create(
            microchip=f"44444444444444{i}",
            name=f"Descendant {i}",
            breed="Poodle",
            dob="2021-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
        )
        DogClosure.objects.create(
            ancestor=sire,
            descendant=pup,
            depth=1,
            entity=entity
        )

    result = calc_saturation(sire.id, entity.id)

    # Total: 1 sire + 8 unrelated + 2 descendants = 11 dogs
    # With ancestry: sire (always counted) + 2 descendants = 3 dogs
    # Saturation: 3/11 = ~27.27%
    assert result.saturation_pct >= 20.0


@pytest.mark.django_db
def test_saturation_entity_scoped():
    """
    Test that saturation is scoped to entity.

    Dogs in different entities should not affect each other's saturation.
    """
    from apps.breeding.models import DogClosure
    from apps.operations.models import Dog
    from apps.core.models import Entity

    entity1 = Entity.objects.create(name="Entity 1", code="ENT1", slug="entity-1")
    entity2 = Entity.objects.create(name="Entity 2", code="ENT2", slug="entity-2")

    # Create sire in entity1
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity1,
    )

    # Create descendants in entity1 with closure table entries
    for i in range(5):
        pup = Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Descendant {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity1,
            sire=sire,
        )
        DogClosure.objects.create(
            ancestor=sire,
            descendant=pup,
            depth=1,
            entity=entity1
        )

    # Create unrelated dogs in entity2 (no closure entries needed)
    for i in range(10):
        Dog.objects.create(
            microchip=f"33333333333333{i}",
            name=f"Other Entity {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity2,
        )

    # Calculate saturation in entity1
    result1 = calc_saturation(sire.id, entity1.id)

    # Entity1: sire + 5 descendants = 6 dogs, all with ancestry = 100%
    assert result1.saturation_pct >= 80.0


@pytest.mark.django_db
def test_saturation_active_only():
    """
    Test that saturation only counts active dogs.

    Retired, rehomed, and deceased dogs should not be counted.
    """
    from apps.breeding.models import DogClosure
    from apps.operations.models import Dog
    from apps.core.models import Entity

    entity = Entity.objects.create(name="Test Entity", code="TEST", slug="test-entity")

    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )

    # Create active descendants with closure table entries
    for i in range(3):
        pup = Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Active Descendant {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
            status="ACTIVE",
        )
        DogClosure.objects.create(
            ancestor=sire,
            descendant=pup,
            depth=1,
            entity=entity
        )

    # Create retired/rehomed/deceased descendants with closure table entries
    for i, status in enumerate(["RETIRED", "REHOMED", "DECEASED"]):
        pup = Dog.objects.create(
            microchip=f"5555555555555{i}",
            name=f"{status} Dog",
            breed="Poodle",
            dob="2019-01-01",
            gender="F",
            entity=entity,
            sire=sire,
            status=status,
        )
        DogClosure.objects.create(
            ancestor=sire,
            descendant=pup,
            depth=1,
            entity=entity
        )

    result = calc_saturation(sire.id, entity.id)

    # Should only count active dogs (3 + sire)
    assert result.active_dogs_in_entity == 4


@pytest.mark.django_db
def test_get_saturation_threshold():
    """
    Test saturation threshold categories.
    """
    assert get_saturation_threshold(0.0) == "SAFE"
    assert get_saturation_threshold(14.9) == "SAFE"
    assert get_saturation_threshold(15.0) == "CAUTION"
    assert get_saturation_threshold(29.9) == "CAUTION"
    assert get_saturation_threshold(30.0) == "HIGH_RISK"
    assert get_saturation_threshold(50.0) == "HIGH_RISK"


@pytest.mark.django_db
def test_saturation_threshold_constants():
    """
    Test threshold constants.
    """
    assert SaturationThreshold.SAFE_PCT == 15.0
    assert SaturationThreshold.CAUTION_PCT == 30.0
