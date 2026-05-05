"""
Operations models for Wellfond BMS
==================================
Dog, HealthRecord, Vaccination models for Phase 2.
Ground Log models for Phase 3.
"""

import uuid
from datetime import date
import logging

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import Entity, User

logger = logging.getLogger(__name__)


class Dog(models.Model):
    """
    Dog/Pedigree model with entity scoping and self-referential FKs for dam/sire.
    """

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETIRED = "RETIRED", "Retired"
        REHOMED = "REHOMED", "Rehomed"
        DECEASED = "DECEASED", "Deceased"

    class DNAStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUBMITTED = "SUBMITTED", "Submitted"
        RESULTS_RECEIVED = "RESULTS_RECEIVED", "Results Received"
        EXCLUDED = "EXCLUDED", "Excluded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Microchip (unique identifier)
    microchip = models.CharField(
        max_length=15,
        unique=True,
        help_text="Unique microchip number (9-15 digits)",
        db_index=True,
    )

    # Basic info
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    dob = models.DateField(help_text="Date of birth")
    gender = models.CharField(max_length=1, choices=Gender.choices)
    colour = models.CharField(max_length=50, blank=True, default='')
    
    # PDPA: Dog models do not have pdpa_consent as they are farm assets.
    # Personal data is scoped at the Customer/Agreement level.
    
    # Entity (multi-tenancy)
    entity = models.ForeignKey(
        Entity,
        on_delete=models.PROTECT,
        related_name="dogs",
        db_index=True,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    # Pedigree (self-referential)
    dam = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dam_offspring",
        help_text="Mother",
    )
    sire = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sire_offspring",
        help_text="Father",
    )

    # Location/Unit
    unit = models.CharField(max_length=50, blank=True, default='', db_index=True)

    # DNA status
    dna_status = models.CharField(
        max_length=20,
        choices=DNAStatus.choices,
        default=DNAStatus.PENDING,
    )
    dna_notes = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True, default='')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dogs_created",
    )

    class Meta:
        db_table = "dogs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "status"]),
            models.Index(fields=["entity", "breed"]),
            models.Index(fields=["dob"]),
            models.Index(fields=["unit"]),
            models.Index(fields=["microchip"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.microchip})"

    @property
    def age_years(self) -> float:
        """Calculate age in years."""
        today = date.today()
        return (today - self.dob).days / 365.25

    @property
    def age_display(self) -> str:
        """Human-readable age."""
        years = int(self.age_years)
        months = int((self.age_years - years) * 12)
        if years > 0:
            return f"{years}y {months}m"
        return f"{months}m"

    @property
    def rehome_flag(self) -> str | None:
        """
        Rehome flag based on age:
        - None: < 5 years
        - 'yellow': 5-6 years (approaching)
        - 'red': 6+ years (overdue)
        """
        age = self.age_years
        if age >= 6:
            return "red"
        elif age >= 5:
            return "yellow"
        return None


class HealthRecord(models.Model):
    """
    Health observations, vet visits, treatments.
    """

    class Category(models.TextChoices):
        VET_VISIT = "VET_VISIT", "Vet Visit"
        TREATMENT = "TREATMENT", "Treatment"
        OBSERVATION = "OBSERVATION", "Observation"
        EMERGENCY = "EMERGENCY", "Emergency"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="health_records",
    )
    date = models.DateField()
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()

    # Vitals
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(35), MaxValueValidator(45)],
        help_text="Temperature in Celsius",
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
        help_text="Weight in kg",
    )

    vet_name = models.CharField(max_length=100, blank=True)

    # NParks compliance: follow-up tracking
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up veterinary treatment is required",
    )
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled follow-up date",
    )

    # Photos (stored as JSON array of URLs)
    photos = models.JSONField(default=list, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_records_created",
    )

    class Meta:
        db_table = "health_records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["dog", "date"]),
        ]

    def __str__(self):
        return f"{self.category} for {self.dog.name} on {self.date}"


class Vaccination(models.Model):
    """
    Vaccination records with automatic due date calculation.
    """

    class Status(models.TextChoices):
        UP_TO_DATE = "UP_TO_DATE", "Up to Date"
        DUE_SOON = "DUE_SOON", "Due Soon"
        OVERDUE = "OVERDUE", "Overdue"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="vaccinations",
    )
    vaccine_name = models.CharField(max_length=100)
    date_given = models.DateField()
    vet_name = models.CharField(max_length=100, blank=True)

    # Calculated due date
    due_date = models.DateField(null=True, blank=True)

    # Status (auto-calculated)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UP_TO_DATE,
        db_index=True,
    )

    # Notes
    notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vaccinations_created",
    )

    class Meta:
        db_table = "vaccinations"
        ordering = ["-date_given"]
        indexes = [
            models.Index(fields=["dog", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.vaccine_name} for {self.dog.name}"

    def save(self, *args, **kwargs):
        """Auto-calculate due date based on vaccine type."""
        # Import here to avoid circular import
        try:
            from .services.vaccine import calc_vaccine_due
            self.due_date = calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
        except ImportError:
            logger.warning(
                "Vaccine service import failed for %s. "
                "Due date not auto-calculated.",
                self.vaccine_name,
                exc_info=True,
            )
        self.status = self._calculate_status()
        super().save(*args, **kwargs)

    def _calculate_status(self) -> str:
        """Calculate status based on due date."""
        if not self.due_date:
            return self.Status.UP_TO_DATE

        today = date.today()
        days_until = (self.due_date - today).days

        if days_until < 0:
            return self.Status.OVERDUE
        elif days_until <= 30:
            return self.Status.DUE_SOON
        return self.Status.UP_TO_DATE


class DogPhoto(models.Model):
    """
    Photos associated with dogs (profile, health, breeding).
    """

    class Category(models.TextChoices):
        PROFILE = "PROFILE", "Profile"
        HEALTH = "HEALTH", "Health"
        BREEDING = "BREEDING", "Breeding"
        GENERAL = "GENERAL", "General"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    url = models.URLField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    customer_visible = models.BooleanField(
        default=False,
        help_text="Whether this photo is visible to customers",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dog_photos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.category} photo for {self.dog.name}"


# =============================================================================
# Phase 3: Ground Operations Log Models
# =============================================================================


class InHeatLog(models.Model):
    """
    Heat cycle tracking with Draminski DOD2 readings.
    """

    class MatingWindow(models.TextChoices):
        EARLY = "EARLY", "Early"
        RISING = "RISING", "Rising"
        FAST = "FAST", "Fast"
        PEAK = "PEAK", "Peak"
        MATE_NOW = "MATE_NOW", "MATE NOW"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="heat_logs",
    )
    draminski_reading = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        help_text="Draminski DOD2 conductivity reading",
    )
    mating_window = models.CharField(
        max_length=20,
        choices=MatingWindow.choices,
        help_text="Calculated mating window based on thresholds",
    )
    notes = models.TextField(blank=True)

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="heat_logs_created",
    )

    class Meta:
        db_table = "in_heat_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Heat log for {self.dog.name}: {self.mating_window}"


class MatedLog(models.Model):
    """
    Mating record with optional dual-sire tracking.
    """

    class Method(models.TextChoices):
        NATURAL = "NATURAL", "Natural"
        ASSISTED = "ASSISTED", "Assisted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="mating_logs",
    )
    sire = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        related_name="sire_mating_logs",
        help_text="Primary sire",
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    sire2 = models.ForeignKey(
        Dog,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sire2_mating_logs",
        help_text="Optional second sire for dual-sire mating",
    )
    notes = models.TextField(blank=True)

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mating_logs_created",
    )

    class Meta:
        db_table = "mated_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Mating for {self.dog.name} with {self.sire.name}"


class WhelpedLog(models.Model):
    """
    Whelping/litter birth record.
    """

    class Method(models.TextChoices):
        NATURAL = "NATURAL", "Natural"
        C_SECTION = "C_SECTION", "C-Section"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="whelping_logs",
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    alive_count = models.PositiveIntegerField(default=0)
    stillborn_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whelping_logs_created",
    )

    class Meta:
        db_table = "whelped_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Whelping for {self.dog.name}: {self.alive_count} alive"


class WhelpedPup(models.Model):
    """
    Individual pup record within a whelping.
    """

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    log = models.ForeignKey(
        WhelpedLog,
        on_delete=models.CASCADE,
        related_name="pups",
    )
    gender = models.CharField(max_length=1, choices=Gender.choices)
    colour = models.CharField(max_length=50, blank=True)
    birth_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(2.0)],
        help_text="Birth weight in kg",
    )

    class Meta:
        db_table = "whelped_pups"
        ordering = ["id"]

    def __str__(self):
        return f"Pup {self.gender} from {self.log.dog.name}'s litter"


class HealthObsLog(models.Model):
    """
    Quick health observation for ground staff.
    """

    class Category(models.TextChoices):
        LIMPING = "LIMPING", "Limping"
        SKIN = "SKIN", "Skin Issue"
        NOT_EATING = "NOT_EATING", "Not Eating"
        EYE_EAR = "EYE_EAR", "Eye/Ear Issue"
        INJURY = "INJURY", "Injury"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="health_obs_logs",
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(35), MaxValueValidator(45)],
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
    )
    photos = models.JSONField(default=list, blank=True)

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_obs_logs_created",
    )

    class Meta:
        db_table = "health_obs_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Health obs for {self.dog.name}: {self.category}"


class WeightLog(models.Model):
    """
    Quick weight tracking for ground staff.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="weight_logs",
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
        help_text="Weight in kg",
    )

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weight_logs_created",
    )

    class Meta:
        db_table = "weight_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Weight for {self.dog.name}: {self.weight}kg"


class NursingFlagLog(models.Model):
    """
    Nursing/mothering issue flags.
    """

    class Section(models.TextChoices):
        MUM = "MUM", "Mum Problems"
        PUP = "PUP", "Pup Problems"

    class FlagType(models.TextChoices):
        NO_MILK = "NO_MILK", "Not Producing Milk"
        REJECTING_PUP = "REJECTING_PUP", "Rejecting Pup"
        PUP_NOT_FEEDING = "PUP_NOT_FEEDING", "Pup Not Feeding"
        OTHER = "OTHER", "Other"

    class Severity(models.TextChoices):
        SERIOUS = "SERIOUS", "Serious - Requires Immediate Attention"
        MONITORING = "MONITORING", "Monitoring"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="nursing_flag_logs",
    )
    section = models.CharField(max_length=20, choices=Section.choices)
    pup_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional pup number for pup-specific issues",
    )
    flag_type = models.CharField(max_length=30, choices=FlagType.choices)
    photos = models.JSONField(default=list, blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices)

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_flag_logs_created",
    )

    class Meta:
        db_table = "nursing_flag_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return f"Nursing flag for {self.dog.name}: {self.flag_type} ({self.severity})"


class NotReadyLog(models.Model):
    """
    Dog not ready for mating/breeding status.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="not_ready_logs",
    )
    notes = models.TextField(blank=True)
    expected_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected date when dog will be ready",
    )

    # Auto-captured metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="not_ready_logs_created",
    )

    class Meta:
        db_table = "not_ready_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["dog", "created_at"]),
        ]

    def __str__(self):
        return f"Not ready: {self.dog.name}"
