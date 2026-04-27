"""
Farm Saturation Calculator
==========================
Phase 4: Breeding & Genetics Engine

Calculates the percentage of active dogs in an entity that share
ancestry with a given sire. Used to prevent over-saturation of
breeding lines.

Formula:
    Saturation % = (dogs with sire ancestry / total active dogs) * 100

Thresholds:
    - SAFE: < 15%
    - CAUTION: 15-30%
    - HIGH_RISK: > 30%
"""

import logging
from typing import Optional
from uuid import UUID

from django.db import connection

from apps.core.models import Entity
from apps.operations.models import Dog

logger = logging.getLogger(__name__)


class SaturationThreshold:
    """Threshold constants for saturation levels."""
    SAFE_PCT = 15.0
    CAUTION_PCT = 30.0


class SaturationResult:
    """Result container for saturation calculation."""
    def __init__(
        self,
        sire_id: UUID,
        sire_name: str,
        entity_id: UUID,
        entity_name: str,
        saturation_pct: float,
        active_dogs_in_entity: int,
        dogs_with_ancestry: int,
    ):
        self.sire_id = sire_id
        self.sire_name = sire_name
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.saturation_pct = saturation_pct
        self.active_dogs_in_entity = active_dogs_in_entity
        self.dogs_with_ancestry = dogs_with_ancestry

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "sire_id": self.sire_id,
            "sire_name": self.sire_name,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "saturation_pct": self.saturation_pct,
            "threshold": self.get_threshold(),
            "active_dogs_in_entity": self.active_dogs_in_entity,
            "dogs_with_ancestry": self.dogs_with_ancestry,
        }

    def get_threshold(self) -> str:
        """
        Get threshold category based on saturation percentage.

        Returns:
            'SAFE', 'CAUTION', or 'HIGH_RISK'
        """
        if self.saturation_pct < SaturationThreshold.SAFE_PCT:
            return "SAFE"
        elif self.saturation_pct < SaturationThreshold.CAUTION_PCT:
            return "CAUTION"
        else:
            return "HIGH_RISK"

    def get_color(self) -> str:
        """
        Get color code for saturation percentage (for UI).

        Returns:
            Hex color code
        """
        if self.saturation_pct < SaturationThreshold.SAFE_PCT:
            return "#4EAD72"  # Green
        elif self.saturation_pct < SaturationThreshold.CAUTION_PCT:
            return "#D4920A"  # Yellow/Orange
        else:
            return "#D94040"  # Red


def calc_saturation(
    sire_id: UUID,
    entity_id: Optional[UUID] = None,
    generations: int = 5
) -> SaturationResult:
    """
    Calculate farm saturation for a given sire.

    Determines what percentage of active dogs in the entity
    have this sire in their ancestry.

    Args:
        sire_id: UUID of the sire to analyze
        entity_id: Entity to scope the calculation (if None, uses sire's entity)
        generations: Number of generations to consider (default: 5)

    Returns:
        SaturationResult with percentage and counts
    """
    # Get sire info
    sire = Dog.objects.filter(id=sire_id, gender="M").first()
    if not sire:
        raise ValueError(f"Sire not found: {sire_id}")

    # Determine entity
    if entity_id is None:
        entity_id = sire.entity_id

    entity = Entity.objects.filter(id=entity_id).first()
    if not entity:
        raise ValueError(f"Entity not found: {entity_id}")

    # Calculate using raw SQL for performance
    with connection.cursor() as cursor:
        # Count active dogs in entity
        cursor.execute("""
            SELECT COUNT(*)
            FROM dogs
            WHERE entity_id = %s
            AND status = 'ACTIVE'
            AND gender IN ('M', 'F')
        """, [entity_id])
        active_dogs = cursor.fetchone()[0]

        if active_dogs == 0:
            # No active dogs - saturation is 0
            return SaturationResult(
                sire_id=sire_id,
                sire_name=sire.name,
                entity_id=entity_id,
                entity_name=entity.name,
                saturation_pct=0.0,
                active_dogs_in_entity=0,
                dogs_with_ancestry=0,
            )

        # Count dogs that have this sire as an ancestor
        cursor.execute("""
            SELECT COUNT(DISTINCT d.id)
            FROM dogs d
            JOIN dog_closure dc ON dc.descendant_id = d.id
            WHERE d.entity_id = %s
            AND d.status = 'ACTIVE'
            AND d.gender IN ('M', 'F')
            AND dc.ancestor_id = %s
            AND dc.depth <= %s
        """, [entity_id, sire_id, generations])
        dogs_with_ancestry = cursor.fetchone()[0]

        # Also count the sire itself (if in same entity and active)
        cursor.execute("""
            SELECT COUNT(*)
            FROM dogs
            WHERE id = %s
            AND entity_id = %s
            AND status = 'ACTIVE'
        """, [sire_id, entity_id])
        sire_in_entity = cursor.fetchone()[0]

        # Add sire to count if in entity
        if sire_in_entity:
            dogs_with_ancestry = min(dogs_with_ancestry + 1, active_dogs)

        # Calculate percentage
        saturation_pct = (dogs_with_ancestry / active_dogs) * 100

        result = SaturationResult(
            sire_id=sire_id,
            sire_name=sire.name,
            entity_id=entity_id,
            entity_name=entity.name,
            saturation_pct=round(saturation_pct, 2),
            active_dogs_in_entity=active_dogs,
            dogs_with_ancestry=dogs_with_ancestry,
        )

        logger.debug(
            f"Saturation for sire {sire.name} in {entity.name}: "
            f"{saturation_pct:.2f}% ({dogs_with_ancestry}/{active_dogs})"
        )

        return result


def calc_saturation_by_chip(
    sire_chip: str,
    entity_code: Optional[str] = None
) -> SaturationResult:
    """
    Calculate saturation using microchip number.

    Args:
        sire_chip: Microchip of the sire
        entity_code: Entity code (e.g., 'HOLDINGS', 'KATONG', 'THOMSON')

    Returns:
        SaturationResult
    """
    # Find sire by chip
    sire = Dog.objects.filter(microchip=sire_chip, gender="M").first()
    if not sire:
        raise ValueError(f"Sire not found with chip: {sire_chip}")

    # Determine entity
    entity_id = None
    if entity_code:
        entity = Entity.objects.filter(code=entity_code).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_code}")
        entity_id = entity.id

    return calc_saturation(sire.id, entity_id)


def get_entity_saturation_summary(
    entity_id: UUID,
    top_n: int = 10
) -> list:
    """
    Get saturation summary for all sires in an entity.

    Returns top N sires by saturation percentage.

    Args:
        entity_id: Entity UUID
        top_n: Number of top sires to return

    Returns:
        List of dicts with sire info and saturation
    """
    with connection.cursor() as cursor:
        # Get all male dogs in entity
        cursor.execute("""
            SELECT id, name, microchip
            FROM dogs
            WHERE entity_id = %s
            AND gender = 'M'
            AND status = 'ACTIVE'
            ORDER BY name
        """, [entity_id])

        sires = cursor.fetchall()

    # Calculate saturation for each sire
    results = []
    for sire_id, name, microchip in sires:
        try:
            result = calc_saturation(sire_id, entity_id)
            if result.saturation_pct > 0:
                results.append({
                    "sire_id": sire_id,
                    "name": name,
                    "microchip": microchip,
                    "saturation_pct": result.saturation_pct,
                    "threshold": result.get_threshold(),
                    "active_dogs": result.active_dogs_in_entity,
                    "dogs_with_ancestry": result.dogs_with_ancestry,
                })
        except Exception as e:
            logger.warning(f"Failed to calculate saturation for sire {name}: {e}")

    # Sort by saturation descending and return top N
    results.sort(key=lambda x: x["saturation_pct"], reverse=True)
    return results[:top_n]


def get_saturation_threshold(saturation_pct: float) -> str:
    """
    Get threshold category based on saturation percentage.

    Args:
        saturation_pct: Percentage value

    Returns:
        'SAFE', 'CAUTION', or 'HIGH_RISK'
    """
    if saturation_pct < SaturationThreshold.SAFE_PCT:
        return "SAFE"
    elif saturation_pct < SaturationThreshold.CAUTION_PCT:
        return "CAUTION"
    else:
        return "HIGH_RISK"


def get_saturation_color(saturation_pct: float) -> str:
    """
    Get color code for saturation percentage.

    Args:
        saturation_pct: Percentage value

    Returns:
        Hex color code
    """
    if saturation_pct < SaturationThreshold.SAFE_PCT:
        return "#4EAD72"  # Green
    elif saturation_pct < SaturationThreshold.CAUTION_PCT:
        return "#D4920A"  # Yellow/Orange
    else:
        return "#D94040"  # Red
