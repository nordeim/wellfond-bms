"""
Operations Admin - Wellfond BMS
=================================
Django admin configuration for operations models.
"""

from django.contrib import admin

from .models import Dog, DogPhoto, HealthRecord, Vaccination


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    """Dog admin with search and filtering."""
    
    list_display = [
        'microchip', 'name', 'breed', 'gender', 'age_display',
        'entity', 'status', 'unit', 'dna_status'
    ]
    list_filter = [
        'status', 'gender', 'dna_status', 'breed', 'entity'
    ]
    search_fields = ['microchip', 'name', 'breed', 'unit']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('microchip', 'name', 'breed', 'dob', 'gender', 'colour')
        }),
        ('Location', {
            'fields': ('entity', 'unit')
        }),
        ('Status', {
            'fields': ('status', 'dna_status', 'dna_notes')
        }),
        ('Pedigree', {
            'fields': ('dam', 'sire')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'age_display']
    
    autocomplete_fields = ['entity', 'dam', 'sire']
    
    def get_queryset(self, request):
        """Prefetch related for performance."""
        return super().get_queryset(request).select_related(
            'entity', 'dam', 'sire'
        )


class HealthRecordInline(admin.TabularInline):
    """Inline health records for dog admin."""
    model = HealthRecord
    extra = 0
    fields = ['date', 'category', 'description', 'temperature', 'weight', 'vet_name']
    readonly_fields = ['created_at']


class VaccinationInline(admin.TabularInline):
    """Inline vaccinations for dog admin."""
    model = Vaccination
    extra = 0
    fields = ['vaccine_name', 'date_given', 'due_date', 'status', 'vet_name']
    readonly_fields = ['due_date', 'status', 'created_at']


class DogPhotoInline(admin.TabularInline):
    """Inline photos for dog admin."""
    model = DogPhoto
    extra = 0
    fields = ['url', 'category', 'customer_visible', 'created_at']
    readonly_fields = ['created_at']


# Add inlines to DogAdmin
DogAdmin.inlines = [HealthRecordInline, VaccinationInline, DogPhotoInline]


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    """Health record admin."""
    
    list_display = ['dog', 'date', 'category', 'vet_name', 'created_at']
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['dog__name', 'dog__microchip', 'description', 'vet_name']
    date_hierarchy = 'date'
    autocomplete_fields = ['dog']


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    """Vaccination admin."""
    
    list_display = ['dog', 'vaccine_name', 'date_given', 'due_date', 'status', 'created_at']
    list_filter = ['status', 'date_given', 'created_at']
    search_fields = ['dog__name', 'dog__microchip', 'vaccine_name', 'vet_name']
    date_hierarchy = 'date_given'
    autocomplete_fields = ['dog']
    
    readonly_fields = ['due_date', 'status']


@admin.register(DogPhoto)
class DogPhotoAdmin(admin.ModelAdmin):
    """Dog photo admin with thumbnail preview."""
    
    list_display = ['dog', 'category', 'customer_visible', 'thumbnail_preview', 'created_at']
    list_filter = ['category', 'customer_visible', 'created_at']
    search_fields = ['dog__name', 'dog__microchip']
    autocomplete_fields = ['dog']
    
    def thumbnail_preview(self, obj):
        """Show thumbnail preview."""
        from django.utils.html import format_html
        return format_html(
            '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
            obj.url
        )
    thumbnail_preview.short_description = 'Preview'
