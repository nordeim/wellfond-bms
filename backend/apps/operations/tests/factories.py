"""
Test factories for operations models.
"""

import factory
from datetime import date, timedelta

from apps.core.tests.factories import EntityFactory, UserFactory
from apps.operations.models import Dog, HealthRecord, Vaccination, DogPhoto


class DogFactory(factory.django.DjangoModelFactory):
    """Factory for creating test dogs."""
    
    class Meta:
        model = Dog
    
    microchip = factory.Sequence(lambda n: f"900000000{n:06d}")
    name = factory.Faker('first_name')
    breed = factory.Faker('word')
    dob = factory.LazyAttribute(lambda _: date.today() - timedelta(days=365 * 3))
    gender = factory.Iterator(['M', 'F'])
    colour = factory.Faker('color_name')
    entity = factory.SubFactory(EntityFactory)
    status = Dog.Status.ACTIVE
    unit = factory.Iterator(['A', 'B', 'C'])
    dna_status = Dog.DNAStatus.PENDING
    notes = factory.Faker('sentence')
    
    @factory.post_generation
    def set_age_display(obj, create, extracted, **kwargs):
        """Set age display after creation."""
        obj.age_display = obj._meta.model.age_display.fget(obj)


class HealthRecordFactory(factory.django.DjangoModelFactory):
    """Factory for creating test health records."""
    
    class Meta:
        model = HealthRecord
    
    dog = factory.SubFactory(DogFactory)
    date = factory.LazyAttribute(lambda _: date.today())
    category = factory.Iterator([
        HealthRecord.Category.VET_VISIT,
        HealthRecord.Category.TREATMENT,
        HealthRecord.Category.OBSERVATION,
    ])
    description = factory.Faker('paragraph')
    temperature = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=36, max_value=40)
    weight = factory.Faker('pydecimal', left_digits=2, right_digits=2, min_value=1, max_value=50)
    vet_name = factory.Faker('name')
    photos = factory.List([])
    created_by = factory.SubFactory(UserFactory)


class VaccinationFactory(factory.django.DjangoModelFactory):
    """Factory for creating test vaccinations."""
    
    class Meta:
        model = Vaccination
    
    dog = factory.SubFactory(DogFactory)
    vaccine_name = factory.Iterator(['DHPP', 'Rabies', 'Bordetella', 'Leptospirosis'])
    date_given = factory.LazyAttribute(lambda _: date.today() - timedelta(days=30))
    vet_name = factory.Faker('name')
    due_date = factory.LazyAttribute(lambda _: date.today() + timedelta(days=335))
    status = Vaccination.Status.UP_TO_DATE
    notes = factory.Faker('sentence')
    created_by = factory.SubFactory(UserFactory)


class DogPhotoFactory(factory.django.DjangoModelFactory):
    """Factory for creating test dog photos."""
    
    class Meta:
        model = DogPhoto
    
    dog = factory.SubFactory(DogFactory)
    url = factory.Faker('image_url')
    category = factory.Iterator([
        DogPhoto.Category.PROFILE,
        DogPhoto.Category.HEALTH,
        DogPhoto.Category.GENERAL,
    ])
    customer_visible = factory.Iterator([True, False])
    uploaded_by = factory.SubFactory(UserFactory)
