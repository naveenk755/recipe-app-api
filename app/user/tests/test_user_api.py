from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
USER_PROFILE_URL = reverse('user:me')


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

    def test_auth_req_url(self):
        """Testing API which require authentication"""

        res = self.apiClient.get(USER_PROFILE_URL, {})
        self.assertTrue(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Testing APIs which require authentication"""

    def setUp(self):
        self.apiClient = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass',
            name='Test Name'
        )
        self.apiClient.force_authenticate(self.user)

    def test_get_user(self):
        """Testing API to fet the logged in user detail"""

        res = self.apiClient.get(USER_PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_update_user(self):
        """Testing API to update the logged in user profile"""

        payload = {
            'name': 'New test name',
            'email': 'test2@example.com'
        }

        res = self.apiClient.patch(USER_PROFILE_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload['email'])
        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_post_disabled(self):
        """Testing API for method POST"""

        res = self.apiClient.post(USER_PROFILE_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
