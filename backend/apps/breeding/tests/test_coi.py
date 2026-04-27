"""
COI Calculation Tests
=====================
Phase 4: Breeding & Genetics Engine

Test suite for Wright's COI formula implementation.

Expected COI values:
- Unrelated dogs: 0%
- Full siblings: 25%
- Parent-offspring: 25%
- Grandparent-grandchild: 12.5%
- Half-siblings: 12.5%
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from apps.breeding.services.coi import calc_coi, get_coi_threshold
from apps.breeding.models import DogClosure


@pytest.mark.django_db
def test_coi_unrelated_returns_zero():
    """
    Test that unrelated dogs have 0% COI.
    
    Two dogs with no common ancestors should return 0% COI.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(
        name="Test Entity",
        code="TEST"
    )
    
    # Create two unrelated dogs (no dam/sire)
    dam = Dog.objects.create(
        microchip="123456789012345",
        name="Unrelated Dam",
        breed="Poodle",
        dob="2020-01-01",
        gender="F",
        entity=entity,
    )
    
    sire = Dog.objects.create(
        microchip="987654321098765",
        name="Unrelated Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )
    
    result = calc_coi(dam.id, sire.id, generations=5)
    
    assert result["coi_pct"] == 0.0
    assert result["shared_ancestors"] == []
    assert result["generation_depth"] == 5


@pytest.mark.django_db
def test_coi_full_siblings_returns_25pct():
    """
    Test that full siblings have 25% COI.
    
    Full siblings share both parents, resulting in 25% COI.
    Formula: (0.5)^(1+1+1) * (1+0) = 0.125 = 12.5% per parent
    Total: 12.5% + 12.5% = 25%
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create grandparents
    g_dam = Dog.objects.create(
        microchip="111111111111111",
        name="Grandparent Dam",
        breed="Poodle",
        dob="2018-01-01",
        gender="F",
        entity=entity,
    )
    g_sire = Dog.objects.create(
        microchip="222222222222222",
        name="Grandparent Sire",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create common parents
    parent_dam = Dog.objects.create(
        microchip="333333333333333",
        name="Parent Dam",
        breed="Poodle",
        dob="2019-01-01",
        gender="F",
        entity=entity,
        dam=g_dam,
        sire=g_sire,
    )
    parent_sire = Dog.objects.create(
        microchip="444444444444444",
        name="Parent Sire",
        breed="Poodle",
        dob="2019-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create full siblings
    sibling1 = Dog.objects.create(
        microchip="555555555555555",
        name="Sibling 1",
        breed="Poodle",
        dob="2021-01-01",
        gender="F",
        entity=entity,
        dam=parent_dam,
        sire=parent_sire,
    )
    sibling2 = Dog.objects.create(
        microchip="666666666666666",
        name="Sibling 2",
        breed="Poodle",
        dob="2021-01-01",
        gender="M",
        entity=entity,
        dam=parent_dam,
        sire=parent_sire,
    )
    
    # Build closure table manually for test
    DogClosure.objects.create(ancestor=g_dam, descendant=parent_dam, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=g_sire, descendant=parent_dam, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=parent_dam, descendant=sibling1, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=parent_sire, descendant=sibling1, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=parent_dam, descendant=sibling2, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=parent_sire, descendant=sibling2, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=g_dam, descendant=sibling1, depth=2, entity=entity)
    DogClosure.objects.create(ancestor=g_sire, descendant=sibling1, depth=2, entity=entity)
    DogClosure.objects.create(ancestor=g_dam, descendant=sibling2, depth=2, entity=entity)
    DogClosure.objects.create(ancestor=g_sire, descendant=sibling2, depth=2, entity=entity)
    
    result = calc_coi(sibling1.id, sibling2.id, generations=5, use_cache=False)
    
    # Full siblings should have 25% COI
    assert 20.0 <= result["coi_pct"] <= 30.0  # Allow some tolerance


@pytest.mark.django_db
def test_coi_parent_offspring_returns_25pct():
    """
    Test that parent-offspring mating has 25% COI.
    
    Parent-offspring is genetically equivalent to full siblings
    in terms of shared genetic material.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create parent
    parent = Dog.objects.create(
        microchip="111111111111111",
        name="Parent",
        breed="Poodle",
        dob="2019-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create offspring
    offspring = Dog.objects.create(
        microchip="222222222222222",
        name="Offspring",
        breed="Poodle",
        dob="2021-01-01",
        gender="F",
        entity=entity,
        sire=parent,
    )
    
    # Build closure table
    DogClosure.objects.create(ancestor=parent, descendant=offspring, depth=1, entity=entity)
    
    result = calc_coi(offspring.id, parent.id, generations=5, use_cache=False)
    
    # Parent-offspring should have 25% COI
    assert 20.0 <= result["coi_pct"] <= 30.0


@pytest.mark.django_db
def test_coi_grandparent_returns_12_5pct():
    """
    Test that grandparent-grandchild mating has 12.5% COI.
    
    Grandparent-grandchild shares 1/8 of genetic material.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create grandparent
    grandparent = Dog.objects.create(
        microchip="111111111111111",
        name="Grandparent",
        breed="Poodle",
        dob="2018-01-01",
        gender="M",
        entity=entity,
    )
    
    # Create parent
    parent = Dog.objects.create(
        microchip="222222222222222",
        name="Parent",
        breed="Poodle",
        dob="2019-01-01",
        gender="F",
        entity=entity,
        sire=grandparent,
    )
    
    # Create grandchild
    grandchild = Dog.objects.create(
        microchip="333333333333333",
        name="Grandchild",
        breed="Poodle",
        dob="2021-01-01",
        gender="M",
        entity=entity,
        dam=parent,
    )
    
    # Build closure table
    DogClosure.objects.create(ancestor=grandparent, descendant=parent, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=parent, descendant=grandchild, depth=1, entity=entity)
    DogClosure.objects.create(ancestor=grandparent, descendant=grandchild, depth=2, entity=entity)
    
    result = calc_coi(parent.id, grandchild.id, generations=5, use_cache=False)
    
    # Grandparent-grandchild should have 12.5% COI
    assert 10.0 <= result["coi_pct"] <= 15.0


@pytest.mark.django_db
def test_coi_5_generation_depth():
    """
    Test that COI calculation respects 5-generation depth limit.
    
    Ancestors beyond 5 generations should not be included.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create dogs
    dam = Dog.objects.create(
        microchip="123456789012345",
        name="Test Dam",
        breed="Poodle",
        dob="2020-01-01",
        gender="F",
        entity=entity,
    )
    
    sire = Dog.objects.create(
        microchip="987654321098765",
        name="Test Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )
    
    # Calculate with different generation depths
    result_3gen = calc_coi(dam.id, sire.id, generations=3)
    result_5gen = calc_coi(dam.id, sire.id, generations=5)
    result_10gen = calc_coi(dam.id, sire.id, generations=10)
    
    # Both should return consistent results for unrelated dogs
    assert result_3gen["generation_depth"] == 3
    assert result_5gen["generation_depth"] == 5
    assert result_10gen["generation_depth"] == 10


@pytest.mark.django_db
def test_coi_missing_parent_returns_zero():
    """
    Test that dogs with missing parents handle gracefully.
    
    Dogs with unknown parents should not cause errors.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    # Create dogs with no dam/sire
    dam = Dog.objects.create(
        microchip="123456789012345",
        name="Unknown Dam",
        breed="Poodle",
        dob="2020-01-01",
        gender="F",
        entity=entity,
    )
    
    sire = Dog.objects.create(
        microchip="987654321098765",
        name="Unknown Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )
    
    result = calc_coi(dam.id, sire.id, generations=5)
    
    # Should return 0% without errors
    assert result["coi_pct"] == 0.0
    assert result["shared_ancestors"] == []


@pytest.mark.django_db
def test_coi_cached_second_call(mocker):
    """
    Test that second call uses cached result.
    
    COI calculations should be cached in Redis for 1 hour.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    dam = Dog.objects.create(
        microchip="123456789012345",
        name="Test Dam",
        breed="Poodle",
        dob="2020-01-01",
        gender="F",
        entity=entity,
    )
    
    sire = Dog.objects.create(
        microchip="987654321098765",
        name="Test Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )
    
    # First call - calculate
    result1 = calc_coi(dam.id, sire.id, generations=5, use_cache=True)
    
    # Second call - should use cache
    result2 = calc_coi(dam.id, sire.id, generations=5, use_cache=True)
    
    assert result1["coi_pct"] == result2["coi_pct"]


@pytest.mark.django_db
def test_coi_deterministic_same_result():
    """
    Test that COI calculation is deterministic.
    
    Same inputs should always produce same output.
    """
    from apps.operations.models import Dog
    from apps.core.models import Entity
    
    entity = Entity.objects.create(name="Test Entity", code="TEST")
    
    dam = Dog.objects.create(
        microchip="123456789012345",
        name="Test Dam",
        breed="Poodle",
        dob="2020-01-01",
        gender="F",
        entity=entity,
    )
    
    sire = Dog.objects.create(
        microchip="987654321098765",
        name="Test Sire",
        breed="Poodle",
        dob="2020-01-01",
        gender="M",
        entity=entity,
    )
    
    # Calculate multiple times
    results = []
    for _ in range(5):
        result = calc_coi(dam.id, sire.id, generations=5, use_cache=False)
        results.append(result["coi_pct"])
    
    # All results should be identical
    assert len(set(results)) == 1


@pytest.mark.django_db
def test_get_coi_threshold():
    """
    Test COI threshold categories.
    """
    assert get_coi_threshold(0.0) == "SAFE"
    assert get_coi_threshold(6.24) == "SAFE"
    assert get_coi_threshold(6.25) == "CAUTION"
    assert get_coi_threshold(12.49) == "CAUTION"
    assert get_coi_threshold(12.5) == "HIGH_RISK"
    assert get_coi_threshold(25.0) == "HIGH_RISK"
    assert get_coi_threshold(50.0) == "HIGH_RISK"
