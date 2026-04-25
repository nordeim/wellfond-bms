"""
Core models for Wellfond BMS
============================
User model with RBAC and entity-based access control
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with RBAC and entity scoping support.
    Implements Phase 1: Core Auth, BFF Proxy & RBAC requirements.
    """

    # Role choices as per Phase 1 spec
    class Role(models.TextChoices):
        MANAGEMENT = "management", "Management"
        ADMIN = "admin", "Admin"
        SALES = "sales", "Sales"
        GROUND = "ground", "Ground"
        VET = "vet", "Vet"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20, blank=True)

    # Primary role (RBAC)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.GROUND,
        help_text="User's primary role for RBAC",
    )

    # Primary entity (for default scoping)
    entity = models.ForeignKey(
        "Entity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_users",
        help_text="User's primary entity for data scoping",
    )

    # PDPA consent tracking
    pdpa_consent = models.BooleanField(
        default=False, help_text="User has consented to PDPA terms"
    )
    pdpa_consent_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the given roles."""
        return self.role in roles

    def get_entity_id(self) -> uuid.UUID | None:
        """Get user's primary entity ID for scoping."""
        return self.entity_id if self.entity else None


class Entity(models.Model):
    """
    Business entity (Holdings, Katong, Thomson, etc.)
    Implements multi-tenancy with entity-level scoping.
    """

    class Code(models.TextChoices):
        HOLDINGS = "HOLDINGS", "Holdings"
        KATONG = "KATONG", "Katong"
        THOMSON = "THOMSON", "Thomson"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20, choices=Code.choices, unique=True, default=Code.HOLDINGS
    )
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    is_holding = models.BooleanField(default=False)

    # Singapore AVS License
    avs_license_number = models.CharField(max_length=50, blank=True)
    avs_license_expiry = models.DateField(null=True, blank=True)

    # Singapore GST rate (default 9%)
    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.09,
        help_text="GST rate as decimal (e.g., 0.09 for 9%)",
    )

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


class AuditLog(models.Model):
    """
    Immutable audit log for compliance.
    No UPDATE or DELETE allowed (enforced via save/delete overrides).
    """

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        VIEW = "view", "View"
        EXPORT = "export", "Export"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor who performed the action
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )

    # Action details
    action = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamp (immutable)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        return (
            f"{self.action} {self.resource_type} by {self.actor} at {self.created_at}"
        )

    def save(self, *args, **kwargs):
        """Prevent updates - audit logs are append-only."""
        if self.pk and not kwargs.get("force_insert"):
            raise ValueError("AuditLog entries cannot be updated")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion - audit logs are immutable."""
        raise ValueError("AuditLog entries cannot be deleted")
