from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client


class AdminSiteTests(TestCase):
    """Class for testing admin"""

    def setUp(self):
        """Setting up user and client"""

        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            'admin@example.com',
            'testpass1'
        )

        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass2',
            name='normal user'
        )

    def test_users_list(self):
        """Testing the users list site"""

        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_update_page(self):
        """Testing the user details admin page"""

        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_add_user_page(self):
        """Testing add user admin page"""

        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
