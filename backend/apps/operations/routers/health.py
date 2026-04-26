"""
Health Router - Wellfond BMS
==============================
Health records and vaccinations endpoints.
"""

from ninja import Router, Query
from ninja.errors import HttpError

from apps.core.permissions import scope_entity
from apps.operations.models import Dog, HealthRecord, Vaccination, DogPhoto
from ..schemas import (
    DogPhotoCreate, DogPhotoListResponse, DogPhotoSummary,
    HealthRecordCreate, HealthRecordListResponse, HealthRecordSummary,
    VaccinationCreate, VaccinationListResponse, VaccinationWithDueDate,
)

router = Router(tags=["health"])


def _get_current_user(request):
    """Get current user from session cookie."""
    from apps.core.auth import get_authenticated_user
    return get_authenticated_user(request)


def _check_permission(request, dog: Dog = None):
    """Check if user has access to the dog."""
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    if dog and user.role != 'management':
        if str(dog.entity_id) != str(user.entity_id):
            raise HttpError(403, "Access denied")
    
    return user


# =============================================================================
# Health Records
# =============================================================================

@router.get("/{dog_id}/health", response=HealthRecordListResponse)
def list_health_records(
    request,
    dog_id: str,
    category: str = None,
    limit: int = Query(default=50, le=100)
):
    """
    List health records for a dog.
    
    Query params:
    - category: Filter by category (VET_VISIT, TREATMENT, OBSERVATION, EMERGENCY)
    - limit: Maximum records to return (default 50, max 100)
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    qs = dog.health_records.select_related('created_by').all()
    
    if category:
        qs = qs.filter(category=category.upper())
    
    qs = qs.order_by('-date', '-created_at')[:limit]
    
    return {"count": len(qs), "results": qs}


@router.post("/{dog_id}/health", response=HealthRecordSummary)
def create_health_record(request, dog_id: str, data: HealthRecordCreate):
    """
    Add a health record for a dog.
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    record = HealthRecord.objects.create(
        dog=dog,
        date=data.date,
        category=data.category,
        description=data.description,
        temperature=data.temperature,
        weight=data.weight,
        vet_name=data.vet_name or '',
        photos=data.photos or [],
        created_by=user,
    )
    
    return record


# =============================================================================
# Vaccinations
# =============================================================================

@router.get("/{dog_id}/vaccinations", response=VaccinationListResponse)
def list_vaccinations(
    request,
    dog_id: str,
    status: str = None,
    limit: int = Query(default=50, le=100)
):
    """
    List vaccinations for a dog with calculated due dates.
    
    Query params:
    - status: Filter by status (UP_TO_DATE, DUE_SOON, OVERDUE)
    - limit: Maximum records to return (default 50, max 100)
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    qs = dog.vaccinations.all()
    
    if status:
        qs = qs.filter(status=status.upper())
    
    qs = qs.order_by('-date_given')[:limit]
    
    # Calculate days_until_due for each
    results = []
    from datetime import date
    today = date.today()
    
    for vac in qs:
        days_until = None
        is_overdue = False
        is_due_soon = False
        
        if vac.due_date:
            days_until = (vac.due_date - today).days
            is_overdue = days_until < 0
            is_due_soon = 0 <= days_until <= 30
        
        results.append({
            **{
                "id": str(vac.id),
                "vaccine_name": vac.vaccine_name,
                "date_given": vac.date_given,
                "vet_name": vac.vet_name,
                "due_date": vac.due_date,
                "status": vac.status,
            },
            "days_until_due": days_until,
            "is_overdue": is_overdue,
            "is_due_soon": is_due_soon,
        })
    
    return {"count": len(results), "results": results}


@router.post("/{dog_id}/vaccinations", response=VaccinationWithDueDate)
def create_vaccination(request, dog_id: str, data: VaccinationCreate):
    """
    Add a vaccination for a dog.
    
    Due date is auto-calculated based on vaccine type.
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    vaccination = Vaccination.objects.create(
        dog=dog,
        vaccine_name=data.vaccine_name,
        date_given=data.date_given,
        vet_name=data.vet_name or '',
        due_date=data.due_date,  # Will be recalculated in save()
        notes=data.notes or '',
        created_by=user,
    )
    
    # Return with calculated fields
    from datetime import date
    today = date.today()
    days_until = None
    is_overdue = False
    is_due_soon = False
    
    if vaccination.due_date:
        days_until = (vaccination.due_date - today).days
        is_overdue = days_until < 0
        is_due_soon = 0 <= days_until <= 30
    
    return {
        "id": str(vaccination.id),
        "vaccine_name": vaccination.vaccine_name,
        "date_given": vaccination.date_given,
        "vet_name": vaccination.vet_name,
        "due_date": vaccination.due_date,
        "status": vaccination.status,
        "days_until_due": days_until,
        "is_overdue": is_overdue,
        "is_due_soon": is_due_soon,
    }


# =============================================================================
# Photos
# =============================================================================

@router.get("/{dog_id}/photos", response=DogPhotoListResponse)
def list_photos(
    request,
    dog_id: str,
    category: str = None,
    customer_visible_only: bool = False,
    limit: int = Query(default=50, le=100)
):
    """
    List photos for a dog.
    
    Query params:
    - category: Filter by category (PROFILE, HEALTH, BREEDING, GENERAL)
    - customer_visible_only: Only show customer-visible photos
    - limit: Maximum records to return (default 50, max 100)
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    qs = dog.photos.all()
    
    if category:
        qs = qs.filter(category=category.upper())
    
    if customer_visible_only:
        qs = qs.filter(customer_visible=True)
    
    qs = qs.order_by('-created_at')[:limit]
    
    return {"count": len(qs), "results": qs}


@router.post("/{dog_id}/photos", response=DogPhotoSummary)
def upload_photo(request, dog_id: str, data: DogPhotoCreate):
    """
    Add a photo for a dog.
    
    Note: Actual file upload would be handled separately (e.g., to S3/R2).
    This endpoint assumes the file is already uploaded and provides the URL.
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    _check_permission(request, dog)
    
    photo = DogPhoto.objects.create(
        dog=dog,
        url=data.url,
        category=data.category or 'GENERAL',
        customer_visible=data.customer_visible or False,
        uploaded_by=user,
    )
    
    return photo
