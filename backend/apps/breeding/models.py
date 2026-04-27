"""
Breeding & Genetics models for Wellfond BMS
============================================
Phase 4: Breeding & Genetics Engine

Core models:
- BreedingRecord: Mating records with dual-sire support
- Litter: Whelping events
- Puppy: Individual pups within litters
- DogClosure: Pedigree closure table for COI calculations
- MateCheckOverride: Audit trail for mate checker overrides
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import Entity, User
from apps.operations.models import Dog


class BreedingRecord(models.Model):
    """
    Breeding/mating record supporting dual-sire breeding.
    Tracks dam, up to 2 sires, breeding method, and confirmation status.
    """

    class Method(models.TextChoices):
        NATURAL = "NATURAL", "Natural"
        ASSISTED = "ASSISTED", "Assisted"

    class ConfirmedSire(models.TextChoices):
        SIRE1 = "SIRE1", "Sire 1"
        SIRE2 = "SIRE2", "Sire 2"
        UNCONFIRMED = "UNCONFIRMED", "Unconfirmed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dam = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        related_name="dam_breedings",
        help_text="Female parent",
        limit_choices_to={"gender": "F"},
    )

    sire1 = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        related_name="sire1_breedings",
        help_text="Primary male parent",
        limit_choices_to={"gender": "M"},
    )

    sire2 = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sire2_breedings",
        help_text="Secondary male parent (dual-sire breeding)",
        limit_choices_to={"gender": "M"},
    )

    date = models.DateField(help_text="Breeding/mating date")
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.NATURAL,
        help_text="Breeding method",
    )

    confirmed_sire = models.CharField(
        max_length=20,
        choices=ConfirmedSire.choices,
        default=ConfirmedSire.UNCONFIRMED,
        help_text="Which sire was confirmed as the father",
    )

    expected_whelp_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected whelping date (breeding date + 63 days)",
    )

    notes = models.TextField(blank=True, help_text="Additional notes")

    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="breeding_records",
        db_index=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_breedings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "breeding_records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["dam", "date"]),
            models.Index(fields=["sire1", "date"]),
            models.Index(fields=["entity", "date"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        sire_info = f"{self.sire1.name}"
        if self.sire2:
            sire_info += f" / {self.sire2.name}"
        return f"{self.dam.name} x {sire_info} ({self.date})"

    def save(self, *args, **kwargs):
        if self.date and not self.expected_whelp_date:
            from datetime import timedelta
            self.expected_whelp_date = self.date + timedelta(days=63)
        if not self.entity_id and self.dam:
            self.entity = self.dam.entity
        super().save(*args, **kwargs)

    @property
    def has_litter(self):
        return hasattr(self, "litter")


class Litter(models.Model):
    """
    Whelping/litter record linked to a breeding record.
    Tracks delivery details and puppy counts.
    """

    class DeliveryMethod(models.TextChoices):
        NATURAL = "NATURAL", "Natural"
        C_SECTION = "C_SECTION", "C-Section"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    breeding_record = models.OneToOneField(
        BreedingRecord,
        on_delete=models.PROTECT,
        related_name="litter",
        help_text="Associated breeding record",
    )

    whelp_date = models.DateField(help_text="Actual whelping date")
    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.NATURAL,
        help_text="Delivery method",
    )

    alive_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of puppies born alive",
    )
    stillborn_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of stillborn puppies",
    )

    total_count = models.PositiveIntegerField(
        default=0,
        help_text="Total puppies (alive + stillborn)",
    )

    notes = models.TextField(blank=True, help_text="Delivery notes")

    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="litters",
        db_index=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_litters",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "litters"
        ordering = ["-whelp_date", "-created_at"]
        indexes = [
            models.Index(fields=["entity", "whelp_date"]),
            models.Index(fields=["breeding_record"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Litter: {self.breeding_record.dam.name} ({self.whelp_date}) - {self.alive_count} alive"

    def save(self, *args, **kwargs):
        self.total_count = self.alive_count + self.stillborn_count
        if not self.entity_id and self.breeding_record:
            self.entity = self.breeding_record.entity
        super().save(*args, **kwargs)


class Puppy(models.Model):
    """
    Individual puppy record within a litter.
    Tracks microchip, gender, color, birth weight, and paternity.
    """

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class PaternityMethod(models.TextChoices):
        VISUAL = "VISUAL", "Visual Assessment"
        DNA = "DNA", "DNA Test"
        UNCONFIRMED = "UNCONFIRMED", "Unconfirmed"

    class Status(models.TextChoices):
        ALIVE = "ALIVE", "Alive"
        REHOMED = "REHOMED", "Rehomed"
        DECEASED = "DECEASED", "Deceased"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    litter = models.ForeignKey(
        Litter,
        on_delete=models.PROTECT,
        related_name="puppies",
        help_text="Litter this puppy belongs to",
    )

    microchip = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        help_text="Microchip number (assigned later)",
        db_index=True,
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        help_text="Puppy gender",
    )
    colour = models.CharField(max_length=50, help_text="Coat color/markings")
    birth_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Birth weight in grams",
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    confirmed_sire = models.CharField(
        max_length=20,
        choices=BreedingRecord.ConfirmedSire.choices,
        default=BreedingRecord.ConfirmedSire.UNCONFIRMED,
        help_text="Which sire is the confirmed father",
    )
    paternity_method = models.CharField(
        max_length=20,
        choices=PaternityMethod.choices,
        default=PaternityMethod.UNCONFIRMED,
        help_text="Method used to determine paternity",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ALIVE,
        help_text="Current puppy status",
    )

    buyer_name = models.CharField(max_length=100, blank=True, help_text="Buyer's name")
    buyer_contact = models.CharField(max_length=100, blank=True, help_text="Buyer's contact")
    sale_date = models.DateField(null=True, blank=True, help_text="Date of sale/rehoming")

    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="puppies",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "puppies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["litter", "gender"]),
            models.Index(fields=["entity", "status"]),
            models.Index(fields=["microchip"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        chip = f" ({self.microchip})" if self.microchip else ""
        return f"Puppy {self.gender}{chip} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.entity_id and self.litter:
            self.entity = self.litter.entity
        super().save(*args, **kwargs)


class DogClosure(models.Model):
    """
    Closure table for ancestry/pedigree calculations.
    Stores all ancestor-descendant paths with depth for efficient COI calculation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ancestor = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="descendant_paths",
        help_text="Ancestor dog",
        db_index=True,
    )
    descendant = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="ancestor_paths",
        help_text="Descendant dog",
        db_index=True,
    )

    depth = models.PositiveIntegerField(
        help_text="Generations between ancestor and descendant",
        validators=[MinValueValidator(0)],
    )

    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="closure_entries",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dog_closure"
        ordering = ["ancestor", "descendant"]
        unique_together = ["ancestor", "descendant"]
        indexes = [
            models.Index(fields=["ancestor", "descendant", "depth"]),
            models.Index(fields=["entity", "ancestor"]),
            models.Index(fields=["entity", "descendant"]),
            models.Index(fields=["depth"]),
        ]

    def __str__(self):
        return f"{self.ancestor.name} -> {self.descendant.name} (depth {self.depth})"


class MateCheckOverride(models.Model):
    """
    Audit trail for mate checker overrides.
    Records when staff override the system's COI/saturation verdict.
    """

    class Verdict(models.TextChoices):
        SAFE = "SAFE", "Safe"
        CAUTION = "CAUTION", "Caution"
        HIGH_RISK = "HIGH_RISK", "High Risk"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dam = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        related_name="dam_override_checks",
        limit_choices_to={"gender": "F"},
    )
    sire1 = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        related_name="sire1_override_checks",
        limit_choices_to={"gender": "M"},
    )
    sire2 = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sire2_override_checks",
        limit_choices_to={"gender": "M"},
    )

    coi_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Calculated COI percentage",
    )
    saturation_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Calculated farm saturation percentage",
    )
    verdict = models.CharField(
        max_length=20,
        choices=Verdict.choices,
        help_text="System-calculated verdict",
    )

    override_reason = models.CharField(
        max_length=200,
        help_text="Reason for overriding the verdict",
    )
    override_notes = models.TextField(
        blank=True,
        help_text="Additional notes about the override",
    )

    staff = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mate_check_overrides",
    )

    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="mate_check_overrides",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mate_check_overrides"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "created_at"]),
            models.Index(fields=["dam", "sire1", "created_at"]),
            models.Index(fields=["staff", "created_at"]),
        ]

    def __str__(self):
        return f"Override: {self.dam.name} x {self.sire1.name} ({self.created_at})"

    def save(self, *args, **kwargs):
        if not self.entity_id and self.dam:
            self.entity = self.dam.entity
        super().save(*args, **kwargs)
