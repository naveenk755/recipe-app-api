from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model

from core.models import Recipe

from decimal import Decimal
from recipe.serializers import RecipeSerializer


RECEIPE_URL = reverse('recipe:recipe-list')


def create_sample_recipe(user, **params):
    """Create and return sample recipe"""

    defaults = {
        'title': 'Sample Title',
        'description': 'Sample Description',
        'price': Decimal('10.12'),
        'time_minutes': 22,
        'link': 'http://example.com/recipe.pdf'
    }

    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Testing unauthenticated API Requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECEIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Testing Private Recipe APIs."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Testing retrieving a list of recipes"""

        create_sample_recipe(user=self.user)
        create_sample_recipe(user=self.user)

        res = self.client.get(RECEIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipes_limit_to_user(self):
        """Testing recipe list is limited to authenticated user"""
        other_user = get_user_model().objects.create_user(
            email='test1@example.com',
            password='test1pass'
        )

        create_sample_recipe(user=self.user)
        create_sample_recipe(user=other_user)

        res = self.client.get(RECEIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
