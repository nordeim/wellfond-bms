"""
Breeding & Genetics Admin
========================
Phase 4: Breeding & Genetics Engine

Django admin configuration for breeding models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import BreedingRecord, DogClosure, Litter, MateCheckOverride, Puppy


@admin.register(BreedingRecord)
class BreedingRecordAdmin(admin.ModelAdmin):
    """Admin configuration for BreedingRecord."""

    list_display = [
        "dam",
        "sire1",
        "sire2_display",
        "date",
        "method",
        "confirmed_sire",
        "expected_whelp_date",
        "has_litter_display",
        "entity",
        "created_by",
    ]
    list_filter = [
        "method",
        "confirmed_sire",
        "date",
        "entity",
        "created_at",
    ]
    search_fields = [
        "dam__name",
        "dam__microchip",
        "sire1__name",
        "sire1__microchip",
        "sire2__name",
        "sire2__microchip",
        "notes",
    ]
    raw_id_fields = ["dam", "sire1", "sire2", "entity", "created_by"]
    date_hierarchy = "date"
    ordering = ["-date"]

    fieldsets = (
        ("Parents", {
            "fields": (("dam", "sire1"), "sire2"),
        }),
        ("Breeding Details", {
            "fields": ("date", "method", "confirmed_sire", "expected_whelp_date"),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
        ("Metadata", {
            "fields": ("entity", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ["created_at", "updated_at", "expected_whelp_date"]

    def sire2_display(self, obj):
        """Display sire2 or dash if None."""
        return obj.sire2.name if obj.sire2 else "—"
    sire2_display.short_description = "Sire 2"

    def has_litter_display(self, obj):
        """Display litter status as boolean."""
        if obj.has_litter:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">—</span>')
    has_litter_display.short_description = "Litter"
    has_litter_display.boolean = True


class PuppyInline(admin.TabularInline):
    """Inline admin for puppies within a litter."""

    model = Puppy
    extra = 0
    fields = [
        "gender",
        "colour",
        "birth_weight",
        "confirmed_sire",
        "paternity_method",
        "status",
        "microchip",
    ]
    raw_id_fields = ["entity"]


@admin.register(Litter)
class LitterAdmin(admin.ModelAdmin):
    """Admin configuration for Litter."""

    list_display = [
        "id",
        "breeding_record_link",
        "dam_name",
        "whelp_date",
        "delivery_method",
        "alive_count",
        "stillborn_count",
        "total_count",
        "puppy_count",
        "entity",
    ]
    list_filter = [
        "delivery_method",
        "whelp_date",
        "entity",
        "created_at",
    ]
    search_fields = [
        "breeding_record__dam__name",
        "breeding_record__sire1__name",
        "notes",
    ]
    raw_id_fields = ["breeding_record", "entity", "created_by"]
    date_hierarchy = "whelp_date"
    ordering = ["-whelp_date"]
    inlines = [PuppyInline]

    fieldsets = (
        ("Breeding Record", {
            "fields": ("breeding_record",),
        }),
        ("Delivery", {
            "fields": (("whelp_date", "delivery_method"),),
        }),
        ("Puppy Counts", {
            "fields": (("alive_count", "stillborn_count", "total_count"),),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
        ("Metadata", {
            "fields": ("entity", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ["total_count", "created_at", "updated_at"]

    def breeding_record_link(self, obj):
        """Display breeding record as link."""
        return f"{obj.breeding_record.dam.name} x {obj.breeding_record.sire1.name}"
    breeding_record_link.short_description = "Breeding"

    def dam_name(self, obj):
        """Display dam name."""
        return obj.breeding_record.dam.name
    dam_name.short_description = "Dam"

    def puppy_count(self, obj):
        """Display puppy count."""
        return obj.puppies.count()
    puppy_count.short_description = "Puppies"


@admin.register(Puppy)
class PuppyAdmin(admin.ModelAdmin):
    """Admin configuration for Puppy."""

    list_display = [
        "id",
        "microchip_display",
        "gender",
        "colour",
        "birth_weight",
        "litter_link",
        "confirmed_sire",
        "paternity_method",
        "status",
        "entity",
    ]
    list_filter = [
        "gender",
        "confirmed_sire",
        "paternity_method",
        "status",
        "entity",
        "created_at",
    ]
    search_fields = [
        "microchip",
        "colour",
        "litter__breeding_record__dam__name",
        "litter__breeding_record__sire1__name",
    ]
    raw_id_fields = ["litter", "entity"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Litter", {
            "fields": ("litter",),
        }),
        ("Puppy Details", {
            "fields": (("gender", "colour"), "birth_weight", "microchip"),
        }),
        ("Paternity", {
            "fields": (("confirmed_sire", "paternity_method"),),
        }),
        ("Status", {
            "fields": ("status",),
        }),
        ("Buyer", {
            "fields": ("sale_date",),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("entity", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ["created_at", "updated_at"]

    def litter_link(self, obj):
        """Display litter as link."""
        return f"Litter {obj.litter.whelp_date}"
    litter_link.short_description = "Litter"

    def microchip_display(self, obj):
        """Display microchip or placeholder."""
        return obj.microchip or format_html('<em style="color: gray;">Not assigned</em>')
    microchip_display.short_description = "Microchip"


@admin.register(DogClosure)
class DogClosureAdmin(admin.ModelAdmin):
    """Admin configuration for DogClosure (read-only)."""

    list_display = [
        "ancestor_link",
        "descendant_link",
        "depth",
        "entity",
        "created_at",
    ]
    list_filter = [
        "depth",
        "entity",
        "created_at",
    ]
    search_fields = [
        "ancestor__name",
        "ancestor__microchip",
        "descendant__name",
        "descendant__microchip",
    ]
    raw_id_fields = ["ancestor", "descendant", "entity"]
    ordering = ["ancestor", "descendant"]

    readonly_fields = ["ancestor", "descendant", "depth", "entity", "created_at"]

    def has_add_permission(self, request):
        """Prevent manual creation - only via Celery task."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent manual editing - read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return request.user.is_superuser

    def ancestor_link(self, obj):
        """Display ancestor as link."""
        return obj.ancestor.name
    ancestor_link.short_description = "Ancestor"

    def descendant_link(self, obj):
        """Display descendant as link."""
        return obj.descendant.name
    descendant_link.short_description = "Descendant"


@admin.register(MateCheckOverride)
class MateCheckOverrideAdmin(admin.ModelAdmin):
    """Admin configuration for MateCheckOverride (read-only)."""

    list_display = [
        "id",
        "mating_display",
        "coi_pct",
        "saturation_pct",
        "verdict",
        "staff",
        "created_at",
    ]
    list_filter = [
        "verdict",
        "entity",
        "created_at",
    ]
    search_fields = [
        "dam__name",
        "dam__microchip",
        "sire1__name",
        "sire1__microchip",
        "override_reason",
        "staff__email",
    ]
    raw_id_fields = ["dam", "sire1", "sire2", "staff", "entity"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        ("Mating", {
            "fields": (("dam", "sire1"), "sire2"),
        }),
        ("Calculated Values", {
            "fields": (("coi_pct", "saturation_pct"), "verdict"),
        }),
        ("Override Details", {
            "fields": ("override_reason", "override_notes"),
        }),
        ("Staff", {
            "fields": ("staff",),
        }),
        ("Metadata", {
            "fields": ("entity", "created_at"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = [
        "dam", "sire1", "sire2",
        "coi_pct", "saturation_pct", "verdict",
        "override_reason", "override_notes",
        "staff", "entity", "created_at",
    ]

    def has_add_permission(self, request):
        """Prevent manual creation - only via API."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent manual editing - read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for superuser only."""
        return request.user.is_superuser

    def mating_display(self, obj):
        """Display mating as formatted string."""
        sire2_info = f" / {obj.sire2.name}" if obj.sire2 else ""
        return f"{obj.dam.name} x {obj.sire1.name}{sire2_info}"
    mating_display.short_description = "Mating"
