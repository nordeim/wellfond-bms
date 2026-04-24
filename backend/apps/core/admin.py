"""
Core admin configuration - Wellfond BMS
========================================
User, Entity, and AuditLog admin interfaces.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Entity, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with RBAC support.
    Phase 1: Core Auth, BFF Proxy & RBAC
    """

    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "entity",
        "is_active",
        "pdpa_consent",
        "created_at",
    ]
    list_filter = [
        "role",
        "is_active",
        "pdpa_consent",
        "created_at",
    ]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "mobile",
    ]
    ordering = ["-created_at"]
    list_select_related = ["entity"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "mobile",
                )
            },
        ),
        (
            "RBAC & Entity",
            {
                "fields": (
                    "role",
                    "entity",
                    "pdpa_consent",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                    "entity",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """
    Entity admin with AVS license and GST tracking.
    """

    list_display = [
        "name",
        "code",
        "is_active",
        "is_holding",
        "gst_rate",
        "avs_license_number",
        "avs_license_expiry",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_holding",
        "created_at",
    ]
    search_fields = [
        "name",
        "code",
        "avs_license_number",
    ]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            "Entity Info",
            {
                "fields": (
                    "name",
                    "code",
                    "slug",
                    "is_active",
                    "is_holding",
                )
            },
        ),
        (
            "Singapore Compliance",
            {
                "fields": (
                    "avs_license_number",
                    "avs_license_expiry",
                    "gst_rate",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "address",
                    "phone",
                    "email",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Audit log admin (read-only).
    Compliance: Immutable audit trail.
    """

    list_display = [
        "action",
        "actor",
        "resource_type",
        "resource_id",
        "ip_address",
        "created_at",
    ]
    list_filter = [
        "action",
        "created_at",
    ]
    search_fields = [
        "actor__email",
        "resource_type",
        "resource_id",
    ]
    date_hierarchy = "created_at"

    # Read-only - audit logs are immutable
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
