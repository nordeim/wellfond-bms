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
        
        # Create session-authenticated client (Ninja-compatible)
        from django.http import HttpRequest
        from apps.core.auth import SessionManager, AuthenticationService

        request = HttpRequest()
        request.method = "POST"
        request.META["SERVER_NAME"] = "localhost"
        request.META["SERVER_PORT"] = "8000"

        session_key, _ = SessionManager.create_session(self.user, request)
        self.client.cookies[AuthenticationService.COOKIE_NAME] = session_key
    
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


@pytest.mark.django_db
class TestAuditFixValidation(TestCase):
    """RED phase tests — validate audit findings before fixes are applied.

    These tests codify the anti-patterns found in the May-3 audit report.
    They are designed to FAIL in the current codebase and PASS after fixes.
    All tests are runnable in CI (no external dependencies beyond pytest + Django).
    """

    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity, role='admin')
        self.dog = DogFactory(entity=self.entity, name='Original Dog')
        self.client = Client()
        # Create session-authenticated client (Ninja-compatible)
        from django.http import HttpRequest
        from apps.core.auth import SessionManager, AuthenticationService

        request = HttpRequest()
        request.method = "POST"
        request.META["SERVER_NAME"] = "localhost"
        request.META["SERVER_PORT"] = "8000"

        session_key, _ = SessionManager.create_session(self.user, request)
        self.client.cookies[AuthenticationService.COOKIE_NAME] = session_key

    # ------------------------------------------------------------------
    # Test 1: Pydantic v2 — endpoint must NOT use .dict()
    # ------------------------------------------------------------------
    def test_update_dog_uses_model_dump_not_dict(self):
        """GREEN: update_dog calls .model_dump() on the incoming data object.

        Verified via source inspection — the deprecated .dict() must be absent
        and .model_dump() must be present in the update_dog function body.
        """
        import inspect
        from apps.operations.routers.dogs import update_dog

        source = inspect.getsource(update_dog)

        self.assertNotIn(
            '.dict(', source,
            'Deprecated .dict() still present in update_dog — need .model_dump()',
        )
        self.assertIn(
            '.model_dump(', source,
            'Expected .model_dump() not found in update_dog after fix',
        )
        # Specific check for the exact call we expect
        self.assertIn(
            'data.model_dump(exclude_unset=True)', source,
            'Expected data.model_dump(exclude_unset=True) not found',
        )

    # Test 2: Pydantic v2 — direct assertion via code inspection
    # (now covered by test_update_dog_uses_model_dump_not_dict above)

    # ------------------------------------------------------------------
    # Test 3: Q import must be at module level, not inside functions
    # ------------------------------------------------------------------
    def test_q_is_imported_at_module_level(self):
        """RED: `from django.db.models import Q` must be top-level."""
        import apps.operations.routers.dogs as dogs_module

        body_source = dogs_module.__file__
        with open(body_source) as fh:
            source = fh.read()

        # Module-level Q import should exist exactly once in import block
        self.assertIn('from django.db.models import Q', source)

        # Q should NOT still be imported inside function bodies (lazy imports)
        import_count = source.count('from django.db.models import Q')
        self.assertEqual(
            import_count, 1,
            f'Expected 1 top-level Q import, found {import_count} — '
            f'function-body imports not yet removed',
        )

    # ------------------------------------------------------------------
    # Test 4: list_dogs must NOT prefetch vaccinations/photos
    # ------------------------------------------------------------------
    def test_list_dogs_queryset_no_prefetch_vaccinations(self):
        """RED: list_dogs returns DogSummary; vaccinations/photos not needed.

        The summary endpoint should not pay the cost of prefetch_related on
        vaccinations and photos — those are only needed by get_dog (detail).
        """
        import inspect
        from apps.operations.routers.dogs import list_dogs

        source = inspect.getsource(list_dogs)
        # After fix: no prefetch_related('vaccinations', 'photos')
        self.assertNotIn(
            "prefetch_related('vaccinations', 'photos')",
            source,
            'list_dogs still prefetches vaccinations & photos — '
            'remove for list (summary) endpoint, keep only in get_dog (detail)',
        )
        # list_dogs should still use select_related for the summary fields
        self.assertIn(
            "select_related('entity'",
            source,
            'list_dogs lost its required select_related — entity scoping still needed',
        )

    # ------------------------------------------------------------------
    # Test 5: Auth helpers consolidated — use get_authenticated_user directly
    # ------------------------------------------------------------------
    def test_auth_helpers_use_get_authenticated_user(self):
        """GREEN: No lazy import — _get_current_user removed, _check_permission uses direct call."""
        import inspect
        import apps.operations.routers.dogs as dogs_module

        # _get_current_user no longer exists in the module
        self.assertFalse(
            hasattr(dogs_module, '_get_current_user'),
            '_get_current_user helper still exists — should be consolidated into _check_permission',
        )

        source = inspect.getsource(dogs_module._check_permission)
        # Must NOT contain a lazy import inside the function body
        self.assertNotIn(
            'from apps.core.auth import',
            source,
            '_check_permission still contains lazy import — '
            'should use module-level get_authenticated_user import',
        )
        # Must call get_authenticated_user directly
        self.assertIn(
            'get_authenticated_user(request)',
            source,
            '_check_permission does not call get_authenticated_user directly',
        )

    def test_auth_module_imports_get_authenticated_user(self):
        """RED: Module imports must include get_authenticated_user."""
        import apps.operations.routers.dogs as dogs_module

        self.assertTrue(
            hasattr(dogs_module, 'get_authenticated_user') or
            'get_authenticated_user' in str(dogs_module.__dict__),
            'Module-level get_authenticated_user import missing',
        )

    def test_auth_module_does_not_import_authentication_service_into_dogs(self):
        """RED: AuthenticationService import should not be in dogs.py (unused)."""
        import apps.operations.routers.dogs as dogs_module

        self.assertFalse(
            hasattr(dogs_module, 'AuthenticationService'),
            'Unused AuthenticationService import still present in dogs module',
        )
