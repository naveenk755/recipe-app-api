from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag
from recipe.serializers import TagSerializer

TAG_URL = reverse('recipe:tag-list')


def get_tag_detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@example.com', password='testpass'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class PublicTagApiTest(TestCase):
    """Testing unauthenticated api"""

    def setUp(self):
        self.client = APIClient()

    def test_get_tags(self):
        """Testing tag list api without authentication"""

        res = self.client.get(TAG_URL)
        self.assertTrue(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTest(TestCase):
    """Testing authenticated tag APIs."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_tag_list_api(self):
        """Testing api to fetch tags."""

        Tag.objects.create(user=self.user, name='Tag 1')
        Tag.objects.create(user=self.user, name='Tag 2')

        res = self.client.get(TAG_URL)
        recipes = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tag_list_api_restrict_to_user(self):
        """Testing api to fetch tags restricted to authenticated user."""

        other_user = create_user(
            email='user2@example.com', password='password2')

        Tag.objects.create(user=other_user, name='Tag 1')
        Tag.objects.create(user=self.user, name='Tag 2')

        res = self.client.get(TAG_URL)
        recipes = Tag.objects.filter(user=self.user).order_by('-name')
        serializer = TagSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_tag_api(self):
        """Testing api to update a tag."""

        tag = Tag.objects.create(user=self.user, name='Tag 1')
        new_name = 'Tag 2'
        payload = {
            'name': new_name
        }
        res = self.client.patch(get_tag_detail_url(tag.id), payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(new_name, tag.name)

    def test_delete_tag(self):
        """Testing api to delete tag."""

        tag = Tag.objects.create(user=self.user, name='test tag')
        del_url = get_tag_detail_url(tag.id)
        res = self.client.delete(del_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
