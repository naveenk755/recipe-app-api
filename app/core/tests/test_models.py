from django.test import TestCase
from django.contrib.auth import get_user_model

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
