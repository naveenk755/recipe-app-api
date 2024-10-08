from django.test import TestCase
from django.contrib.auth import get_user_model

from unittest.mock import patch

from core import models
from decimal import Decimal


def create_new_user(email='test@example.com', password='testpass'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        """Testing user creation with email"""

        email = "test@example.com"
        password = "test123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Testing email normalization"""

        sample_emails = [
            ('test1@EXAMPLE.COM', 'test1@example.com'),
            ('Test2@example.com', 'Test2@example.com'),
            ('TEST3@example.com', 'TEST3@example.com'),
            ('test4@example.com', 'test4@example.com')
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email=email, password='sample123')
            self.assertEqual(expected, user.email)

    def test_value_error_for_blank_email(self):
        """Testing blank email validation"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='sample123')

    def test_create_super_user(self):
        """Testing super user creation"""

        user = get_user_model().objects.create_superuser('super@example.com', 'sample123')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_recipe(self):
        """Testing Recipe model creation"""

        recipe = models.Recipe.objects.create(
            user=create_new_user(),
            title='test title',
            description='test description',
            time_minutes=5,
            price=Decimal('1.5')
        )

        self.assertEqual(recipe.title, str(recipe))

    def test_create_tag(self):
        """Testing Tag model creation"""

        tag = models.Tag.objects.create(
            name='test tag',
            user=create_new_user()
        )

        self.assertTrue(models.Tag.objects.filter(id=tag.id).exists())
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Testing Ingredient model creation"""

        ingredient = models.Ingredient.objects.create(
            user=create_new_user(),
            name='Ingredient1'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_model_file_name_uuid(self, mock_uuid):
        """Testing generated image path."""

        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
