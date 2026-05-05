"""
Dogs Router - Wellfond BMS
============================
CRUD endpoints for dog management with entity scoping.
"""

from django.db.models import Q
from ninja import Router, Query
from ninja.errors import HttpError

from apps.core.auth import get_authenticated_user
from apps.core.permissions import (
    require_admin, scope_entity, scope_entity_for_list
)
from apps.operations.models import Dog
from ..schemas import (
    DogCreate, DogDetailResponse, DogFilterParams,
    DogListResponse, DogSummary, DogUpdate
)

router = Router(tags=["dogs"])


def _check_permission(request, allowed_roles=None):
    """Check if user has required authentication and role."""
    user = get_authenticated_user(request)

    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")

    if allowed_roles and user.role not in allowed_roles:
        raise HttpError(403, "Permission denied")

    return user


@router.get("/", response=DogListResponse)
def list_dogs(
    request,
    filters: Query[DogFilterParams] = None,
    page: int = 1,
    per_page: int = 25
):
    """
    List dogs with filtering, sorting, and pagination.
    
    Query params:
    - status: Filter by status (ACTIVE, RETIRED, REHOMED, DECEASED)
    - entity: Filter by entity ID (management only)
    - breed: Filter by breed
    - gender: Filter by gender (M/F)
    - search: Search chip or name (partial match)
    - unit: Filter by unit
    - page: Page number (default 1)
    - per_page: Items per page (default 25, max 100)
    """
    user = _check_permission(request)
    
    # Cap per_page
    per_page = min(per_page, 100)
    
    # Base queryset
    qs = Dog.objects.select_related('entity', 'dam', 'sire')
    
    # Apply entity scoping
    if user.role == 'management' and filters and filters.entity:
        # Management can filter by specific entity
        qs = qs.filter(entity_id=filters.entity)
    else:
        # Others see only their entity
        qs = scope_entity(qs, user)
    
    # Apply filters
    if filters:
        if filters.status:
            qs = qs.filter(status=filters.status.upper())
        
        if filters.breed:
            qs = qs.filter(breed__icontains=filters.breed)
        
        if filters.gender:
            qs = qs.filter(gender=filters.gender.upper())
        
        if filters.unit:
            qs = qs.filter(unit__icontains=filters.unit)
        
        if filters.search:
            qs = qs.filter(
                Q(microchip__icontains=filters.search) |
                Q(name__icontains=filters.search)
            )
    
    # Default ordering
    qs = qs.order_by('-created_at')
    
    # Get total count
    total_count = qs.count()
    
    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_qs = qs[start:end]
    
    return {
        "count": total_count,
        "results": list(paginated_qs),
        "page": page,
        "per_page": per_page
    }


@router.get("/{dog_id}", response=DogDetailResponse)
def get_dog(request, dog_id: str):
    """
    Get detailed information about a specific dog.
    
    Includes health records, vaccinations, photos.
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.select_related(
            'entity', 'dam', 'sire', 'created_by'
        ).prefetch_related(
            'health_records', 'vaccinations', 'photos'
        ).get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    # Check entity access
    if user.role != 'management' and str(dog.entity_id) != str(user.entity_id):
        raise HttpError(403, "Access denied")
    
    return dog


@router.post("/", response=DogDetailResponse)
def create_dog(request, data: DogCreate):
    """
    Create a new dog.
    
    Validates:
    - Microchip uniqueness
    - Parent chips exist (if provided)
    - Entity access
    """
    user = _check_permission(request)
    
    # Check entity access
    if user.role != 'management' and str(data.entity_id) != str(user.entity_id):
        raise HttpError(403, "Cannot create dog for different entity")
    
    # Check microchip uniqueness
    if Dog.objects.filter(microchip=data.microchip).exists():
        raise HttpError(422, "Microchip already exists")
    
    # Resolve parents by chip
    dam = None
    sire = None
    
    if data.dam_chip:
        try:
            dam = Dog.objects.get(
                microchip=data.dam_chip,
                entity_id=data.entity_id
            )
        except Dog.DoesNotExist:
            raise HttpError(422, f"Dam with chip {data.dam_chip} not found")
    
    if data.sire_chip:
        try:
            sire = Dog.objects.get(
                microchip=data.sire_chip,
                entity_id=data.entity_id
            )
        except Dog.DoesNotExist:
            raise HttpError(422, f"Sire with chip {data.sire_chip} not found")
    
    # Create dog
    dog = Dog.objects.create(
        microchip=data.microchip,
        name=data.name,
        breed=data.breed,
        dob=data.dob,
        gender=data.gender,
        colour=data.colour or "",
        entity_id=data.entity_id,
        status=data.status or 'ACTIVE',
        dam=dam,
        sire=sire,
        unit=data.unit or "",
        dna_status=data.dna_status or 'PENDING',
        notes=data.notes or "",
        created_by=user,
    )
    
    return dog


@router.patch("/{dog_id}", response=DogDetailResponse)
def update_dog(request, dog_id: str, data: DogUpdate):
    """
    Update a dog's information.
    
    Partial update - only provided fields are updated.
    """
    user = _check_permission(request)
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    # Check entity access
    if user.role != 'management' and str(dog.entity_id) != str(user.entity_id):
        raise HttpError(403, "Access denied")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle parent chips
    if 'dam_chip' in update_data:
        dam_chip = update_data.pop('dam_chip')
        if dam_chip:
            try:
                dog.dam = Dog.objects.get(
                    microchip=dam_chip,
                    entity=dog.entity
                )
            except Dog.DoesNotExist:
                raise HttpError(422, f"Dam with chip {dam_chip} not found")
        else:
            dog.dam = None
    
    if 'sire_chip' in update_data:
        sire_chip = update_data.pop('sire_chip')
        if sire_chip:
            try:
                dog.sire = Dog.objects.get(
                    microchip=sire_chip,
                    entity=dog.entity
                )
            except Dog.DoesNotExist:
                raise HttpError(422, f"Sire with chip {sire_chip} not found")
        else:
            dog.sire = None
    
    # Update remaining fields
    for field, value in update_data.items():
        if field in ['entity_id']:
            # Special handling for entity change
            if user.role != 'management':
                raise HttpError(403, "Only management can change entity")
            dog.entity_id = value
        elif hasattr(dog, field):
            setattr(dog, field, value)
    
    dog.save()
    return dog


@router.delete("/{dog_id}")
def delete_dog(request, dog_id: str):
    """
    Soft-delete a dog by setting status to DECEASED.
    
    Requires admin or management role.
    """
    user = _check_permission(request, ['admin', 'management'])
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    
    # Check entity access
    if user.role != 'management' and str(dog.entity_id) != str(user.entity_id):
        raise HttpError(403, "Access denied")
    
    # Soft delete
    dog.status = Dog.Status.DECEASED
    dog.save()
    
    return {"message": "Dog marked as deceased", "id": str(dog.id)}


@router.get("/search/{query}", response=list[DogSummary])
def search_dogs(request, query: str, limit: int = 10):
    """
    Quick search for dogs by chip or name.
    
    Used for chip search dropdowns.
    """
    user = _check_permission(request)
    
    qs = Dog.objects.filter(
        Q(microchip__icontains=query) |
        Q(name__icontains=query)
    ).select_related('entity')
    
    # Apply entity scoping
    qs = scope_entity(qs, user)
    
    # Limit results
    qs = qs[:limit]
    
    return qs
