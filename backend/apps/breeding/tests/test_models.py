
class TestDogClosureEntityProtect(TestCase):
    """Test that DogClosure entity uses PROTECT (H-007 fix)."""

    def test_entity_cascade_delete_prevents_dogclosure_deletion(self):
        """
        RED: Test that entity deletion is prevented if DogClosure entries exist.
        Should fail initially because entity FK uses CASCADE.
        """
        from apps.core.models import Entity
        from apps.operations.models import Dog
        
        # Create entity
        entity = Entity.objects.create(
            name="Test Entity for DogClosure",
            code="TEST_DC",
            slug="test-entity-dc",
        )
        
        # Create a dog
        dog = Dog.objects.create(
            name="Test Dog",
            gender="M",
            microchip="123456789012345",
            entity=entity,
        )
        
        # Create DogClosure entries
        DogClosure.objects.create(
            ancestor=dog,
            descendant=dog,
            depth=0,
            entity=entity,
        )
        
        # Try to delete entity - should raise ProtectedError after fix
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            entity.delete()

    def test_dogclosure_entity_field_is_protect(self):
        """
        RED: Test that entity field uses PROTECT.
        Should fail initially because it uses CASCADE.
        """
        # Check that entity FK uses PROTECT (not CASCADE)
        for field in DogClosure._meta.fields:
            if field.name == 'entity':
                self.assertEqual(
                    field.remote_field.on_delete,
                    models.PROTECT,
                    "DogClosure.entity should use PROTECT (not CASCADE)"
                )
                break
        else:
            self.fail("Entity field not found in DogClosure")
