"""
Tests for Dog CRUD operations.
"""

import pytest
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from apps.core.tests.factories import EntityFactory, UserFactory
from apps.operations.models import Dog
from apps.operations.tests.factories import DogFactory


@pytest.mark.django_db
class TestDogModel(TestCase):
    """Test Dog model methods and properties."""
    
    def setUp(self):
        self.entity = EntityFactory()
        self.dog = DogFactory(entity=self.entity)
    
    def test_age_calculation(self):
        """Test age is calculated correctly from DOB."""
        # Dog created with 3 years old factory
        self.assertAlmostEqual(self.dog.age_years, 3, delta=0.1)
    
    def test_age_display(self):
        """Test age display formatting."""
        self.assertIn('y', self.dog.age_display)
    
    def test_rehome_flag_red(self):
        """Test red flag for 6+ year old dogs."""
        old_dog = DogFactory(
            entity=self.entity,
            dob=date.today() - timedelta(days=365 * 7)
        )
        self.assertEqual(old_dog.rehome_flag, 'red')
    
    def test_rehome_flag_yellow(self):
        """Test yellow flag for 5-6 year old dogs."""
        aging_dog = DogFactory(
            entity=self.entity,
            dob=date.today() - timedelta(days=365 * 5.5)
        )
        self.assertEqual(aging_dog.rehome_flag, 'yellow')
    
    def test_rehome_flag_none(self):
        """Test no flag for dogs under 5 years."""
        young_dog = DogFactory(
            entity=self.entity,
            dob=date.today() - timedelta(days=365 * 3)
        )
        self.assertIsNone(young_dog.rehome_flag)
    
    def test_microchip_uniqueness(self):
        """Test microchip must be unique."""
        with self.assertRaises(Exception):
            DogFactory(microchip=self.dog.microchip, entity=self.entity)
    
    def test_pedigree_relationships(self):
        """Test dam and sire relationships."""
        dam = DogFactory(entity=self.entity, gender='F')
        sire = DogFactory(entity=self.entity, gender='M')
        
        puppy = DogFactory(
            entity=self.entity,
            dam=dam,
            sire=sire
        )
        
        self.assertEqual(puppy.dam, dam)
        self.assertEqual(puppy.sire, sire)
        self.assertIn(puppy, dam.dam_offspring.all())
        self.assertIn(puppy, sire.sire_offspring.all())


@pytest.mark.django_db
class TestDogEndpoints(TestCase):
    """Test Dog API endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity, role='admin')
        
        # Login to get session
        from apps.core.auth import AuthenticationService
        self.client.force_login(self.user)
    
    def test_list_dogs(self):
        """Test GET /api/v1/dogs/ returns dog list."""
        DogFactory.create_batch(5, entity=self.entity)
        
        response = self.client.get('/api/v1/dogs/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 5)
        self.assertEqual(len(data['results']), 5)
    
    def test_create_dog(self):
        """Test POST /api/v1/dogs/ creates a dog."""
        data = {
            'microchip': '123456789012345',
            'name': 'Test Dog',
            'breed': 'Poodle',
            'dob': '2020-01-01',
            'gender': 'F',
            'entity_id': str(self.entity.id),
        }
        
        response = self.client.post(
            '/api/v1/dogs/',
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['name'], 'Test Dog')
        self.assertEqual(result['microchip'], '123456789012345')
    
    def test_create_dog_duplicate_chip(self):
        """Test creating dog with duplicate microchip fails."""
        existing = DogFactory(entity=self.entity)
        
        data = {
            'microchip': existing.microchip,
            'name': 'Test Dog',
            'breed': 'Poodle',
            'dob': '2020-01-01',
            'gender': 'F',
            'entity_id': str(self.entity.id),
        }
        
        response = self.client.post(
            '/api/v1/dogs/',
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 422)
    
    def test_get_dog_detail(self):
        """Test GET /api/v1/dogs/{id} returns dog details."""
        dog = DogFactory(entity=self.entity)
        
        response = self.client.get(f'/api/v1/dogs/{dog.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], str(dog.id))
        self.assertEqual(data['name'], dog.name)
    
    def test_update_dog(self):
        """Test PATCH /api/v1/dogs/{id} updates a dog."""
        dog = DogFactory(entity=self.entity)
        
        data = {'name': 'Updated Name'}
        
        response = self.client.patch(
            f'/api/v1/dogs/{dog.id}/',
            data=data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Updated Name')
    
    def test_delete_dog_soft_delete(self):
        """Test DELETE /api/v1/dogs/{id} soft-deletes a dog."""
        dog = DogFactory(entity=self.entity)
        
        response = self.client.delete(f'/api/v1/dogs/{dog.id}/')
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh from db
        dog.refresh_from_db()
        self.assertEqual(dog.status, Dog.Status.DECEASED)
    
    def test_search_dogs(self):
        """Test GET /api/v1/dogs/search/{query} searches dogs."""
        DogFactory(entity=self.entity, name='Searchable Dog')
        
        response = self.client.get('/api/v1/dogs/search/Searchable')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Searchable Dog')


@pytest.mark.django_db
class TestEntityScoping(TestCase):
    """Test entity scoping prevents cross-entity data leakage."""
    
    def setUp(self):
        self.entity1 = EntityFactory(code='HOLDINGS')
        self.entity2 = EntityFactory(code='KATONG')
        
        self.user1 = UserFactory(entity=self.entity1, role='admin')
        self.user2 = UserFactory(entity=self.entity2, role='admin')
        self.management = UserFactory(role='management')
        
        DogFactory(entity=self.entity1, name='Entity1 Dog')
        DogFactory(entity=self.entity2, name='Entity2 Dog')
    
    def test_user_sees_only_own_entity_dogs(self):
        """Test user can only see dogs from their entity."""
        from apps.core.permissions import scope_entity
        from apps.operations.models import Dog
        
        all_dogs = Dog.objects.all()
        
        # User1 should only see entity1 dogs
        user1_dogs = scope_entity(all_dogs, self.user1)
        self.assertEqual(user1_dogs.count(), 1)
        self.assertEqual(user1_dogs.first().entity, self.entity1)
        
        # User2 should only see entity2 dogs
        user2_dogs = scope_entity(all_dogs, self.user2)
        self.assertEqual(user2_dogs.count(), 1)
        self.assertEqual(user2_dogs.first().entity, self.entity2)
    
    def test_management_sees_all_dogs(self):
        """Test management can see all dogs."""
        from apps.core.permissions import scope_entity
        from apps.operations.models import Dog
        
        all_dogs = Dog.objects.all()
        
        # Management should see all dogs
        mgmt_dogs = scope_entity(all_dogs, self.management)
        self.assertEqual(mgmt_dogs.count(), 2)


@pytest.mark.django_db
class TestDogFilters(TestCase):
    """Test dog filtering functionality."""
    
    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity, role='admin')
        
        # Create dogs with various attributes
        DogFactory(entity=self.entity, status='ACTIVE', breed='Poodle')
        DogFactory(entity=self.entity, status='RETIRED', breed='Labrador')
        DogFactory(entity=self.entity, gender='M', unit='Unit A')
        DogFactory(entity=self.entity, gender='F', unit='Unit B')
    
    def test_filter_by_status(self):
        """Test filtering by status."""
        active_dogs = Dog.objects.filter(status='ACTIVE')
        self.assertEqual(active_dogs.count(), 1)
    
    def test_filter_by_breed(self):
        """Test filtering by breed."""
        poodles = Dog.objects.filter(breed__icontains='Poodle')
        self.assertEqual(poodles.count(), 1)
    
    def test_filter_by_gender(self):
        """Test filtering by gender."""
        males = Dog.objects.filter(gender='M')
        self.assertEqual(males.count(), 1)
    
    def test_filter_by_unit(self):
        """Test filtering by unit."""
        unit_a = Dog.objects.filter(unit='Unit A')
        self.assertEqual(unit_a.count(), 1)
    
    def test_chip_format_validation(self):
        """Test microchip must be 9-15 digits."""
        from django.core.exceptions import ValidationError
        
        # Try to create with invalid chip
        dog = Dog(
            microchip='123',  # Too short
            name='Invalid',
            breed='Test',
            dob=date.today(),
            gender='M',
            entity=self.entity
        )
        
        # This should raise validation error
        with self.assertRaises(Exception):
            dog.save()
