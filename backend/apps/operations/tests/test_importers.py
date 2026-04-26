"""
Tests for CSV importer functionality.
"""

import csv
import os
import tempfile

import pytest
from django.test import TestCase

from apps.core.tests.factories import EntityFactory, UserFactory
from apps.operations.models import Dog
from apps.operations.services.importers import (
    import_dogs, import_litters, ImportResult, validate_microchip
)


class TestMicrochipValidation(TestCase):
    """Test microchip validation logic."""
    
    def test_valid_microchip(self):
        """Test valid 15-digit microchip."""
        valid, result = validate_microchip('123456789012345')
        self.assertTrue(valid)
        self.assertEqual(result, '123456789012345')
    
    def test_valid_microchip_9_digits(self):
        """Test valid 9-digit microchip."""
        valid, result = validate_microchip('123456789')
        self.assertTrue(valid)
        self.assertEqual(result, '123456789')
    
    def test_invalid_microchip_too_short(self):
        """Test invalid microchip - too short."""
        valid, result = validate_microchip('123')
        self.assertFalse(valid)
        self.assertIn('9-15 digits', result)
    
    def test_invalid_microchip_too_long(self):
        """Test invalid microchip - too long."""
        valid, result = validate_microchip('12345678901234567')
        self.assertFalse(valid)
        self.assertIn('9-15 digits', result)
    
    def test_empty_microchip(self):
        """Test empty microchip fails."""
        valid, result = validate_microchip('')
        self.assertFalse(valid)
        self.assertIn('required', result)
    
    def test_microchip_with_whitespace(self):
        """Test microchip with whitespace is trimmed."""
        valid, result = validate_microchip('  123456789012345  ')
        self.assertTrue(valid)
        self.assertEqual(result, '123456789012345')


@pytest.mark.django_db
class TestImportDogs(TestCase):
    """Test CSV import functionality."""
    
    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity)
    
    def create_test_csv(self, rows):
        """Helper to create test CSV file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False, newline=''
        ) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'microchip', 'name', 'breed', 'dob', 'gender',
                'colour', 'unit', 'dam_chip', 'sire_chip', 'dna_status', 'notes'
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            return f.name
    
    def test_import_valid_dogs(self):
        """Test importing valid dogs from CSV."""
        csv_path = self.create_test_csv([
            {
                'microchip': '900000000000001',
                'name': 'Test Dog 1',
                'breed': 'Poodle',
                'dob': '2020-01-01',
                'gender': 'F',
                'colour': 'White',
                'unit': 'A',
                'dna_status': 'PENDING',
            },
            {
                'microchip': '900000000000002',
                'name': 'Test Dog 2',
                'breed': 'Labrador',
                'dob': '2019-06-15',
                'gender': 'M',
                'colour': 'Black',
                'unit': 'B',
                'dna_status': 'SUBMITTED',
            },
        ])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            self.assertEqual(result.success_count, 2)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.imported_ids), 2)
            
            # Verify dogs were created
            self.assertEqual(Dog.objects.count(), 2)
            
            # Verify dog attributes
            dog1 = Dog.objects.get(microchip='900000000000001')
            self.assertEqual(dog1.name, 'Test Dog 1')
            self.assertEqual(dog1.breed, 'Poodle')
            self.assertEqual(dog1.entity, self.entity)
        finally:
            os.unlink(csv_path)
    
    def test_import_duplicate_chip_in_csv(self):
        """Test import fails on duplicate chips in CSV."""
        csv_path = self.create_test_csv([
            {
                'microchip': '900000000000001',
                'name': 'First Dog',
                'breed': 'Poodle',
                'dob': '2020-01-01',
                'gender': 'F',
            },
            {
                'microchip': '900000000000001',  # Duplicate
                'name': 'Second Dog',
                'breed': 'Labrador',
                'dob': '2019-06-15',
                'gender': 'M',
            },
        ])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            # Should have validation errors, no dogs created
            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.success_count, 0)
            self.assertEqual(Dog.objects.count(), 0)
        finally:
            os.unlink(csv_path)
    
    def test_import_existing_chip_in_database(self):
        """Test import fails when chip already exists in database."""
        # Create existing dog
        DogFactory(entity=self.entity, microchip='900000000000001')
        
        csv_path = self.create_test_csv([
            {
                'microchip': '900000000000001',  # Already exists
                'name': 'New Dog',
                'breed': 'Poodle',
                'dob': '2020-01-01',
                'gender': 'F',
            },
        ])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            # Should have validation error
            self.assertGreater(len(result.errors), 0)
            self.assertEqual(result.success_count, 0)
        finally:
            os.unlink(csv_path)
    
    def test_import_with_parent_resolution(self):
        """Test importing dogs with dam/sire resolution by chip."""
        # Create parent dogs first
        dam = DogFactory(entity=self.entity, microchip='DAM000000000001', gender='F')
        sire = DogFactory(entity=self.entity, microchip='SIRE00000000001', gender='M')
        
        csv_path = self.create_test_csv([
            {
                'microchip': '900000000000001',
                'name': 'Puppy',
                'breed': 'Poodle',
                'dob': '2023-01-01',
                'gender': 'F',
                'dam_chip': dam.microchip,
                'sire_chip': sire.microchip,
            },
        ])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            self.assertEqual(result.success_count, 1)
            
            # Verify puppy has parents
            puppy = Dog.objects.get(microchip='900000000000001')
            self.assertEqual(puppy.dam, dam)
            self.assertEqual(puppy.sire, sire)
        finally:
            os.unlink(csv_path)
    
    def test_import_missing_parent_fails(self):
        """Test import fails when parent chip doesn't exist."""
        csv_path = self.create_test_csv([
            {
                'microchip': '900000000000001',
                'name': 'Puppy',
                'breed': 'Poodle',
                'dob': '2023-01-01',
                'gender': 'F',
                'dam_chip': 'NONEXISTENT0001',  # Doesn't exist
            },
        ])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            # Transaction should rollback, no dogs created
            self.assertEqual(result.success_count, 0)
            self.assertGreater(result.error_count, 0)
            self.assertEqual(Dog.objects.count(), 0)
        finally:
            os.unlink(csv_path)
    
    def test_import_malformed_csv(self):
        """Test import handles malformed CSV gracefully."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False
        ) as f:
            f.write('invalid,csv,content\n')
            f.write('not,a,valid,row\n')
            csv_path = f.name
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            # Should have errors
            self.assertGreater(len(result.errors), 0)
        finally:
            os.unlink(csv_path)
    
    def test_import_empty_csv(self):
        """Test import handles empty CSV."""
        csv_path = self.create_test_csv([])
        
        try:
            result = import_dogs(csv_path, str(self.entity.id))
            
            self.assertEqual(result.success_count, 0)
            self.assertEqual(len(result.errors), 0)  # Empty is not an error
        finally:
            os.unlink(csv_path)


@pytest.mark.django_db
class TestImportLitters(TestCase):
    """Test litter import (placeholder)."""
    
    def test_import_litters_placeholder(self):
        """Test litter import returns placeholder error."""
        result = import_litters('dummy.csv', 'entity-id')
        
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.error_count, 1)
        self.assertIn('not yet implemented', result.errors[0].message)
