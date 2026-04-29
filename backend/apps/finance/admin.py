"""
Finance admin configuration for Wellfond BMS.
"""
from django.contrib import admin
from .models import Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction admin configuration."""
    list_display = [
        "type",
        "amount",
        "entity",
        "gst_component",
        "date",
        "category",
        "created_at",
    ]
    list_filter = [
        "type",
        "entity",
        "category",
        "date",
        "created_at",
    ]
    search_fields = ["description", "entity__name"]
    date_hierarchy = "date"
    readonly_fields = ["created_at"]


@admin.register(IntercompanyTransfer)
class IntercompanyTransferAdmin(admin.ModelAdmin):
    """Intercompany transfer admin configuration."""
    list_display = [
        "from_entity",
        "to_entity",
        "amount",
        "date",
        "created_by",
        "created_at",
    ]
    list_filter = [
        "from_entity",
        "to_entity",
        "date",
        "created_at",
    ]
    search_fields = ["description"]
    date_hierarchy = "date"
    readonly_fields = ["created_at"]


@admin.register(GSTReport)
class GSTReportAdmin(admin.ModelAdmin):
    """GST report admin configuration (read-only)."""
    list_display = [
        "entity",
        "quarter",
        "total_sales",
        "total_gst",
        "generated_at",
        "generated_by",
    ]
    list_filter = [
        "entity",
        "quarter",
        "generated_at",
    ]
    readonly_fields = [
        "entity",
        "quarter",
        "total_sales",
        "total_gst",
        "generated_at",
        "generated_by",
    ]


@admin.register(PNLSnapshot)
class PNLSnapshotAdmin(admin.ModelAdmin):
    """P&L snapshot admin configuration (read-only)."""
    list_display = [
        "entity",
        "month",
        "revenue",
        "cogs",
        "expenses",
        "net",
        "generated_at",
    ]
    list_filter = [
        "entity",
        "month",
        "generated_at",
    ]
    readonly_fields = [
        "entity",
        "month",
        "revenue",
        "cogs",
        "expenses",
        "net",
        "generated_at",
    ]
