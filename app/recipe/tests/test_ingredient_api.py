from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient


INGREDIENT_URL = reverse('recipe:ingredient-list')


def ingredient_detail_url(id):
    return reverse('recipe:ingredient-detail', args=[id])


def create_user(email='test@example.com', password='testpassword'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class PublicIngredientApiTest(TestCase):
    """Testing unauthorized requests"""

    def setUp(self):
        self.client = APIClient()

    def test_get_ingredients(self):
        """Testing unauthorized request to ingredient api"""

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Testing authenticated Ingredient APIs."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_ingredients(self):
        """Testing get ingredients list API"""

        Ingredient.objects.create(user=self.user, name='Ingredient1')
        Ingredient.objects.create(user=self.user, name='Ingredient2')

        ingredients = Ingredient.objects.filter(
            user=self.user).order_by('-name')
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(dict(res.data[0])['name'], ingredients[0].name)
        self.assertEqual(dict(res.data[1])['name'], ingredients[1].name)

    def test_get_ingredients_for_user(self):
        """Testing get ingredients list restricted to user"""

        other_user = create_user(email='other@example.com')
        Ingredient.objects.create(user=other_user, name='Ingredient1')
        ingredient = Ingredient.objects.create(
            user=self.user, name='Ingredient2')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(dict(res.data[0])['name'], ingredient.name)

    def test_update_ingredient(self):
        """testing update ingredient API."""

        new_name = 'Ingredient New'
        ingredient = Ingredient.objects.create(
            user=self.user, name='Ingredient1')

        url = ingredient_detail_url(ingredient.id)
        payload = {'name': new_name}
        res = self.client.patch(url, payload)

        ingredient.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, new_name)

    def test_delete_ingredient(self):
        """Testing delete ingredient API."""

        ingredient = Ingredient.objects.create(
            user=self.user, name='Ingredient1')

        url = ingredient_detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())
