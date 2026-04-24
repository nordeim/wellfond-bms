"""
Core models for Wellfond BMS
============================
User model with entity-based access control
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with entity scoping support.
    Users can belong to multiple entities with different roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    is_entity_admin = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"


class Entity(models.Model):
    """
    Business entity (Holding, Katong, Thomson, etc.)
    Implements multi-tenancy with entity-level scoping.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    is_holding = models.BooleanField(default=False)

    # Singapore AVS License
    avs_license_number = models.CharField(max_length=50, blank=True)
    avs_license_expiry = models.DateField(null=True, blank=True)

    # Contact
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entities"
        verbose_name_plural = "entities"
        ordering = ["name"]

    def __str__(self):
        return self.name


class EntityMembership(models.Model):
    """
    Many-to-many relationship between Users and Entities with role.
    """

    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer"
        STAFF = "staff", "Staff"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="entity_memberships"
    )
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_default = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_memberships"
        unique_together = ["user", "entity"]
        ordering = ["-is_default", "entity__name"]

    def __str__(self):
        return f"{self.user.email} @ {self.entity.name} ({self.role})"
