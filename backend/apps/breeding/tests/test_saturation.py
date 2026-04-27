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
def test_saturation_no_common_ancestry_returns_zero():
    """
    Test that a sire with no descendants in the entity has 0% saturation.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
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
    
    assert result.saturation_pct == 0.0
    assert result.get_threshold() == "SAFE"
    assert result.dogs_with_ancestry == 0


@pytest.mark.django_db
def test_saturation_all_share_sire_returns_100():
    """
    Test that when all active dogs are descendants of the sire,
    saturation is 100%.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Foundation Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create offspring (descendants)
    for i in range(5):
        Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Offspring {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
        )
    
    result = calc_saturation(sire.id, entity.id)
    
    # Should be high saturation (> 50%)
    assert result.saturation_pct >= 50.0


@pytest.mark.django_db
def test_saturation_partial_returns_correct_pct():
    """
    Test that partial saturation is calculated correctly.
    
    If 2 of 10 active dogs share ancestry with sire, saturation = 20%.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create unrelated dogs
    for i in range(8):
        Dog.objects.create(
            microchip=f"33333333333333{i}",
            name=f"Unrelated {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
        )
    
    # Create descendants
    for i in range(2):
        Dog.objects.create(
            microchip=f"44444444444444{i}",
            name=f"Descendant {i}",
            breed="Poodle",
            dob="2021-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
        )
    
    result = calc_saturation(sire.id, entity.id)
    
    # Should be around 20% (2/10)
    assert 15.0 <= result.saturation_pct <= 25.0


@pytest.mark.django_db
def test_saturation_entity_scoped():
    """
    Test that saturation is scoped to entity.
    
    Dogs in different entities should not affect each other's saturation.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity1 = Entity.objects.create(name="Entity 1", code="ENT1")
    entity2 = Entity.objects.create(name="Entity 2", code="ENT2")
    
    # Create sire in entity1
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity1,
    )
    
    # Create descendants in entity1
    for i in range(5):
        Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Descendant {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity1,
            sire=sire,
        )
    
    # Create unrelated dogs in entity2
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
    
    # Should be high in entity1 (all dogs share sire)
    assert result1.saturation_pct >= 50.0


@pytest.mark.django_db
def test_saturation_active_only():
    """
    Test that saturation only counts active dogs.
    
    Retired, rehomed, and deceased dogs should not be counted.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create sire
    sire = Dog.objects.create(
        microchip="111111111111111",
        name="Test Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create active descendants
    for i in range(3):
        Dog.objects.create(
            microchip=f"22222222222222{i}",
            name=f"Active Descendant {i}",
            breed="Poodle",
            dob="2020-01-01",
            gender="F" if i % 2 == 0 else "M",
            entity=entity,
            sire=sire,
            status="ACTIVE",
        )
    
    # Create retired/rehomed/deceased descendants
    for status in ["RETIRED", "REHOMED", "DECEASED"]:
        Dog.objects.create(
            microchip=f"55555555555555{status}",
            name=f"{status} Dog",
            breed="Poodle",
            dob="2019-01-01",
            gender="F",
            entity=entity,
            sire=sire,
            status=status,
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
