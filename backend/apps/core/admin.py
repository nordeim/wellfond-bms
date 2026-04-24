"""
Core admin configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Entity, EntityMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with UUID support."""

    list_display = [
        "email",
        "first_name",
        "last_name",
        "is_entity_admin",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_entity_admin", "is_active", "created_at"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "is_entity_admin"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Entity admin with AVS license tracking."""

    list_display = [
        "name",
        "slug",
        "is_active",
        "is_holding",
        "avs_license_number",
        "created_at",
    ]
    list_filter = ["is_active", "is_holding", "created_at"]
    search_fields = ["name", "avs_license_number"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(EntityMembership)
class EntityMembershipAdmin(admin.ModelAdmin):
    """Entity membership admin."""

    list_display = ["user", "entity", "role", "is_default", "created_at"]
    list_filter = ["role", "is_default", "created_at"]
    search_fields = ["user__email", "entity__name"]
    autocomplete_fields = ["user", "entity"]
