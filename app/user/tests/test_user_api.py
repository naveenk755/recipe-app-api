from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test Public APIs of User app"""

    def setUp(self):
        self.apiClient = APIClient()

    def test_create_user_success(self):
        """Testing successfull user creation"""

        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name'
        }

        res = self.apiClient.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_email_exists(self):
        """Testing duplicate email user creation"""

        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name'
        }
        create_user(**payload)

        res = self.apiClient.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password(self):
        """Testing user creation with short password"""

        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test Name'
        }

        res = self.apiClient.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user)

    def test_token_auth_success(self):
        """Testing success authentication to get token"""

        user_details = dict(email='test@example.com', password='testpass')
        get_user_model().objects.create_user(
            email=user_details['email'], password=user_details['password'])
        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        res = self.apiClient.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_token_auth_failure(self):
        """Testing success authentication to get token"""

        user_details = dict(email='test@example.com', password='testpass')
        get_user_model().objects.create_user(
            email=user_details['email'], password=user_details['password'])
        payload = {
            'email': user_details['email'],
            'password': 'badpass'
        }

        res = self.apiClient.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)
