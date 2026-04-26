"""
CSV Importer service for Wellfond BMS
======================================
Import dogs and litters from CSV files with transactional safety.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from ..models import Dog


@dataclass
class ImportError:
    """Error during CSV import."""
    row: int
    message: str
    field: Optional[str] = None


@dataclass
class ImportResult:
    """Result of CSV import operation."""
    success_count: int = 0
    error_count: int = 0
    errors: List[ImportError] = field(default_factory=list)
    imported_ids: List[str] = field(default_factory=list)


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parse date from various formats."""
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d.%m.%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    
    return None


def validate_microchip(chip: str) -> tuple[bool, str]:
    """Validate microchip format."""
    chip = chip.strip()
    
    if not chip:
        return False, "Microchip is required"
    
    # Remove any non-digit characters
    chip_clean = ''.join(c for c in chip if c.isdigit())
    
    if len(chip_clean) < 9 or len(chip_clean) > 15:
        return False, f"Microchip must be 9-15 digits, got {len(chip_clean)}"
    
    return True, chip_clean


def resolve_parent_by_chip(chip: Optional[str], entity_id: str) -> Optional["Dog"]:
    """Look up a parent dog by microchip."""
    if not chip:
        return None
    
    from ..models import Dog
    
    valid, chip_clean = validate_microchip(chip)
    if not valid:
        return None
    
    try:
        return Dog.objects.get(microchip=chip_clean, entity_id=entity_id)
    except Dog.DoesNotExist:
        return None


def import_dogs(
    csv_path: str,
    default_entity_id: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> ImportResult:
    """
    Import dogs from a CSV file.
    
    CSV columns expected:
    - microchip (required)
    - name (required)
    - breed (required)
    - dob (required, YYYY-MM-DD or DD/MM/YYYY)
    - gender (required, M/F)
    - colour (optional)
    - unit (optional)
    - dam_chip (optional, microchip of mother)
    - sire_chip (optional, microchip of father)
    - dna_status (optional, default PENDING)
    - notes (optional)
    
    Args:
        csv_path: Path to CSV file
        default_entity_id: Default entity for imported dogs
        progress_callback: Optional callback(current, total)
        
    Returns:
        ImportResult with success/error counts
    """
    from ..models import Dog
    
    result = ImportResult()
    
    # Read CSV
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        result.errors.append(ImportError(0, f"Failed to read CSV: {str(e)}"))
        return result
    
    total_rows = len(rows)
    
    # Track microchips for duplicate detection
    seen_chips: set = set()
    
    # Validate all rows first (pre-flight check)
    validated_rows = []
    
    for idx, row in enumerate(rows, start=1):
        errors = []
        
        # Required fields
        microchip = row.get('microchip', '').strip()
        name = row.get('name', '').strip()
        breed = row.get('breed', '').strip()
        dob_str = row.get('dob', '').strip()
        gender = row.get('gender', '').strip().upper()
        
        # Validate microchip
        valid, chip_msg = validate_microchip(microchip)
        if not valid:
            errors.append(ImportError(idx, chip_msg, 'microchip'))
        else:
            # Check for duplicates in CSV
            if chip_msg in seen_chips:
                errors.append(ImportError(
                    idx, f"Duplicate microchip in CSV: {chip_msg}", 'microchip'
                ))
            seen_chips.add(chip_msg)
            
            # Check for existing in database
            if Dog.objects.filter(microchip=chip_msg).exists():
                errors.append(ImportError(
                    idx, f"Microchip already exists: {chip_msg}", 'microchip'
                ))
        
        # Validate name
        if not name:
            errors.append(ImportError(idx, "Name is required", 'name'))
        
        # Validate breed
        if not breed:
            errors.append(ImportError(idx, "Breed is required", 'breed'))
        
        # Validate DOB
        dob = parse_date(dob_str)
        if not dob:
            errors.append(ImportError(
                idx, f"Invalid date format: {dob_str}", 'dob'
            ))
        
        # Validate gender
        if gender not in ['M', 'F']:
            errors.append(ImportError(
                idx, f"Gender must be M or F, got: {gender}", 'gender'
            ))
        
        if errors:
            result.errors.extend(errors)
            continue
        
        validated_rows.append({
            'row': idx,
            'microchip': chip_msg,
            'name': name,
            'breed': breed,
            'dob': dob,
            'gender': gender,
            'colour': row.get('colour', '').strip() or None,
            'unit': row.get('unit', '').strip() or None,
            'dam_chip': row.get('dam_chip', '').strip() or None,
            'sire_chip': row.get('sire_chip', '').strip() or None,
            'dna_status': row.get('dna_status', 'PENDING').upper() or 'PENDING',
            'notes': row.get('notes', '').strip() or None,
        })
    
    # If validation errors, don't proceed
    if result.errors:
        result.error_count = len(result.errors)
        return result
    
    # Import with transaction
    try:
        with transaction.atomic():
            for idx, data in enumerate(validated_rows):
                # Resolve parent chips
                dam = resolve_parent_by_chip(data['dam_chip'], default_entity_id)
                sire = resolve_parent_by_chip(data['sire_chip'], default_entity_id)
                
                # Create dog
                dog = Dog.objects.create(
                    microchip=data['microchip'],
                    name=data['name'],
                    breed=data['breed'],
                    dob=data['dob'],
                    gender=data['gender'],
                    colour=data['colour'],
                    entity_id=default_entity_id,
                    status='ACTIVE',
                    dam=dam,
                    sire=sire,
                    unit=data['unit'],
                    dna_status=data['dna_status'],
                    notes=data['notes'],
                )
                
                result.imported_ids.append(str(dog.id))
                result.success_count += 1
                
                # Progress callback
                if progress_callback:
                    progress_callback(idx + 1, total_rows)
    
    except Exception as e:
        # Transaction rolled back
        result.errors.append(ImportError(0, f"Import failed: {str(e)}"))
        result.error_count += len(validated_rows)
        result.success_count = 0
        result.imported_ids = []
    
    return result


def import_litters(
    csv_path: str,
    default_entity_id: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> ImportResult:
    """
    Import litters from a CSV file.
    
    CSV columns expected:
    - dam_chip (required, mother's microchip)
    - sire_chip (optional, father's microchip)
    - whelp_date (required)
    - delivery_method (optional)
    - alive_count (required)
    - stillborn_count (optional, default 0)
    
    And per-puppy columns:
    - pup1_chip, pup1_gender, pup1_colour, pup1_birth_weight
    - pup2_chip, ... (repeat for each puppy)
    
    Args:
        csv_path: Path to CSV file
        default_entity_id: Default entity for imported litter
        progress_callback: Optional callback(current, total)
        
    Returns:
        ImportResult with success/error counts
    """
    # TODO: Implement when Litter/Puppy models are created in Phase 4
    return ImportResult(
        error_count=1,
        errors=[ImportError(0, "Litter import not yet implemented")]
    )


def import_from_dict(
    dogs_data: List[Dict],
    default_entity_id: str
) -> ImportResult:
    """
    Import dogs from a list of dictionaries (for API usage).
    
    Args:
        dogs_data: List of dog dictionaries
        default_entity_id: Default entity ID
        
    Returns:
        ImportResult
    """
    from ..models import Dog
    
    result = ImportResult()
    
    seen_chips: set = set()
    
    with transaction.atomic():
        for idx, data in enumerate(dogs_data, start=1):
            # Validate required fields
            microchip = data.get('microchip', '').strip()
            name = data.get('name', '').strip()
            
            if not microchip or not name:
                result.errors.append(ImportError(
                    idx, "microchip and name are required"
                ))
                continue
            
            # Check for duplicates
            if microchip in seen_chips:
                result.errors.append(ImportError(
                    idx, f"Duplicate microchip: {microchip}"
                ))
                continue
            seen_chips.add(microchip)
            
            if Dog.objects.filter(microchip=microchip).exists():
                result.errors.append(ImportError(
                    idx, f"Microchip already exists: {microchip}"
                ))
                continue
            
            # Create dog
            try:
                dog = Dog.objects.create(
                    microchip=microchip,
                    name=name,
                    breed=data.get('breed', ''),
                    dob=parse_date(data.get('dob', '')) or datetime.now().date(),
                    gender=data.get('gender', 'M').upper(),
                    colour=data.get('colour'),
                    entity_id=default_entity_id,
                    status='ACTIVE',
                    unit=data.get('unit'),
                    notes=data.get('notes'),
                )
                result.imported_ids.append(str(dog.id))
                result.success_count += 1
            except Exception as e:
                result.errors.append(ImportError(
                    idx, f"Failed to create dog: {str(e)}"
                ))
    
    result.error_count = len(result.errors)
    return result
