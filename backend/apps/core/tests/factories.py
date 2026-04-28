"""Core Test Factories

Factories for creating test data for core models.
"""

import factory
from factory import Faker

from apps.core.models import User, Entity


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory for creating test Entity instances."""

    class Meta:
        model = Entity
        django_get_or_create = ('code',)

    name = factory.LazyAttribute(lambda obj: f"{obj.code.title()} Entity")
    code = factory.Iterator([Entity.Code.HOLDINGS, Entity.Code.KATONG, Entity.Code.THOMSON])
    slug = factory.LazyAttribute(lambda obj: obj.code.lower())
    is_active = True
    is_holding = factory.LazyAttribute(lambda obj: obj.code == Entity.Code.HOLDINGS)
    gst_rate = factory.LazyAttribute(
        lambda obj: 0.00 if obj.code == Entity.Code.THOMSON else 0.09
    )
    address = factory.Faker('address')
    phone = factory.Faker('phone_number')
    email = factory.Faker('company_email')


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test User instances."""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Faker('email')
    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    
    role = factory.Iterator([
        User.Role.MANAGEMENT,
        User.Role.ADMIN,
        User.Role.SALES,
        User.Role.GROUND,
        User.Role.VET,
    ])
    
    entity = factory.SubFactory(EntityFactory)
    is_active = True
    pdpa_consent = True
    
    @factory.post_generation
    def set_entity_for_management(obj, create, extracted, **kwargs):
        """Management users can see all entities, but still need a primary one."""
        if obj.role == User.Role.MANAGEMENT:
            # Ensure entity exists or create holdings as default
            if not obj.entity:
                obj.entity, _ = Entity.objects.get_or_create(
                    code=Entity.Code.HOLDINGS,
                    defaults={'name': 'Holdings', 'slug': 'holdings'}
                )
                if create:
                    obj.save()


class SuperuserFactory(UserFactory):
    """Factory for creating superuser test instances."""

    role = User.Role.MANAGEMENT
    is_staff = True
    is_superuser = True

    @factory.post_generation
    def make_superuser(obj, create, extracted, **kwargs):
        if create:
            obj.is_staff = True
            obj.is_superuser = True
            obj.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin role test users."""
    
    role = User.Role.ADMIN


class SalesUserFactory(UserFactory):
    """Factory for creating sales role test users."""
    
    role = User.Role.SALES


class GroundUserFactory(UserFactory):
    """Factory for creating ground role test users."""
    
    role = User.Role.GROUND


class VetUserFactory(UserFactory):
    """Factory for creating vet role test users."""
    
    role = User.Role.VET
