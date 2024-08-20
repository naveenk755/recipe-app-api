from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        email = "test@example.com"
        password = "test123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
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
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='sample123')

    def test_create_super_user(self):
        user = get_user_model().objects.create_superuser('super@example.com', 'sample123')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
