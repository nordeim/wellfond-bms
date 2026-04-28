"""Django Admin Configuration
==============================
Phase 6: Compliance & NParks Reporting

Admin configurations for compliance models.
All models are read-only after creation (immutable audit trail).
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import NParksSubmission, GSTLedger, PDPAConsentLog


@admin.register(NParksSubmission)
class NParksSubmissionAdmin(admin.ModelAdmin):
    """Admin for NParks submissions."""
    
    list_display = [
        "id",
        "entity",
        "month",
        "status",
        "generated_by",
        "generated_at",
        "submitted_at",
        "locked_at",
    ]
    
    list_filter = [
        "status",
        "entity",
        "month",
        "generated_at",
    ]
    
    search_fields = [
        "entity__name",
        "entity__code",
    ]
    
    readonly_fields = [
        "id",
        "entity",
        "month",
        "generated_at",
        "generated_by",
        "submitted_at",
        "locked_at",
        "mating_sheet_url",
        "puppy_movement_url",
        "vet_treatments_url",
        "puppies_bred_url",
        "dog_movement_url",
    ]
    
    def has_add_permission(self, request):
        """Disable add - only via API."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete - immutable."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change for locked submissions."""
        if obj and obj.status == "LOCKED":
            return False
        return super().has_change_permission(request, obj)
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            "DRAFT": "gray",
            "SUBMITTED": "blue",
            "LOCKED": "green",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    
    status_badge.short_description = "Status"
    
    def download_links(self, obj):
        """Display download links for documents."""
        if obj.status == "DRAFT":
            return "Documents not yet available"
        
        links = []
        if obj.mating_sheet_url:
            links.append(f'<a href="{obj.mating_sheet_url}">Mating Sheet</a>')
        if obj.puppy_movement_url:
            links.append(f'<a href="{obj.puppy_movement_url}">Puppy Movement</a>')
        if obj.vet_treatments_url:
            links.append(f'<a href="{obj.vet_treatments_url}">Vet Treatments</a>')
        if obj.puppies_bred_url:
            links.append(f'<a href="{obj.puppies_bred_url}">Puppies Bred</a>')
        if obj.dog_movement_url:
            links.append(f'<a href="{obj.dog_movement_url}">Dog Movement</a>')
        
        return format_html("<br>".join(links)) if links else "No documents"
    
    download_links.short_description = "Documents"


@admin.register(GSTLedger)
class GSTLedgerAdmin(admin.ModelAdmin):
    """Admin for GST ledger entries."""
    
    list_display = [
        "id",
        "entity",
        "period",
        "source_agreement",
        "total_sales",
        "gst_component",
        "created_at",
    ]
    
    list_filter = [
        "entity",
        "period",
        "created_at",
    ]
    
    search_fields = [
        "entity__name",
        "entity__code",
        "source_agreement__buyer_name",
    ]
    
    readonly_fields = [
        "id",
        "entity",
        "period",
        "source_agreement",
        "total_sales",
        "gst_component",
        "created_at",
    ]
    
    def has_add_permission(self, request):
        """Disable add - only via system."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete - immutable."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable all changes - immutable."""
        return False


@admin.register(PDPAConsentLog)
class PDPAConsentLogAdmin(admin.ModelAdmin):
    """Admin for PDPA consent audit log."""
    
    list_display = [
        "id",
        "customer",
        "action",
        "previous_state",
        "new_state",
        "actor",
        "ip_address",
        "created_at",
    ]
    
    list_filter = [
        "action",
        "previous_state",
        "new_state",
        "created_at",
    ]
    
    search_fields = [
        "customer__name",
        "actor__email",
        "actor__username",
    ]
    
    readonly_fields = [
        "id",
        "customer",
        "action",
        "previous_state",
        "new_state",
        "actor",
        "ip_address",
        "user_agent",
        "created_at",
    ]
    
    def has_add_permission(self, request):
        """Disable add - only via API."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete - immutable."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable all changes - immutable."""
        return False
    
    def action_badge(self, obj):
        """Display action as colored badge."""
        colors = {
            "OPT_IN": "green",
            "OPT_OUT": "red",
        }
        color = colors.get(obj.action, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display(),
        )
    
    action_badge.short_description = "Action"
