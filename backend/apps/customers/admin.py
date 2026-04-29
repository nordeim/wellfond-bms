"""Customers Admin
=================
Phase 7: Customer DB & Marketing Blast

Django admin configurations for customer management.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Customer, CommunicationLog, Segment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin for Customer model."""

    list_display = [
        "id",
        "name",
        "mobile",
        "email",
        "housing_type",
        "pdpa_consent",
        "entity",
        "created_at",
    ]
    list_filter = [
        "pdpa_consent",
        "housing_type",
        "entity",
        "created_at",
    ]
    search_fields = [
        "name",
        "mobile",
        "email",
        "nric",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
    ]

    def pdpa_badge(self, obj):
        """Display PDPA consent as colored badge."""
        if obj.pdpa_consent:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Opted In</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Opted Out</span>'
        )

    pdpa_badge.short_description = "PDPA"


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    """Admin for CommunicationLog (read-only)."""

    list_display = [
        "id",
        "customer",
        "channel",
        "status",
        "subject",
        "created_at",
    ]
    list_filter = [
        "channel",
        "status",
        "created_at",
    ]
    search_fields = [
        "customer__name",
        "customer__mobile",
        "subject",
    ]
    readonly_fields = [
        "id",
        "customer",
        "blast_id",
        "channel",
        "status",
        "subject",
        "message_preview",
        "error_message",
        "external_id",
        "created_at",
        "sent_at",
        "delivered_at",
    ]

    def has_add_permission(self, request):
        """Disable add - only via API."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable delete - immutable."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable changes - immutable."""
        return False

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "PENDING": "gray",
            "SENT": "blue",
            "DELIVERED": "green",
            "BOUNCED": "orange",
            "FAILED": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    """Admin for Segment model."""

    list_display = [
        "id",
        "name",
        "entity",
        "customer_count",
        "count_updated_at",
        "created_at",
    ]
    list_filter = [
        "entity",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = [
        "id",
        "customer_count",
        "count_updated_at",
        "created_at",
        "updated_at",
    ]
