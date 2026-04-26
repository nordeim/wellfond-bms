"""
Operations models for Wellfond BMS
==================================
Dog, HealthRecord, Vaccination models for Phase 2.
"""

import uuid
from datetime import date

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import Entity, User


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
    colour = models.CharField(max_length=50, blank=True)

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
    unit = models.CharField(max_length=50, blank=True, db_index=True)

    # DNA status
    dna_status = models.CharField(
        max_length=20,
        choices=DNAStatus.choices,
        default=DNAStatus.PENDING,
    )
    dna_notes = models.TextField(blank=True)

    # Notes
    notes = models.TextField(blank=True)

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
            # Service not yet available, skip auto-calculation
            pass
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
