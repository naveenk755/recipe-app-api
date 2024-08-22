from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model

from core.models import Recipe, Tag

from decimal import Decimal
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECEIPE_URL = reverse('recipe:recipe-list')


def create_user(email='test@example.com', password='testpasswoed'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


def get_recipe_detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


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
        self.user = create_user()
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

        other_user = create_user(email='otheruser@example.com')

        create_sample_recipe(user=self.user)
        create_sample_recipe(user=other_user)

        res = self.client.get(RECEIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipe_detail_api(self):
        """Testing API to fetch Recipe Details."""

        recipe = create_sample_recipe(user=self.user)
        res = self.client.get(get_recipe_detail_url(recipe_id=recipe.id))

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_api(self):
        """Testing API to create a Recipe."""

        payload = {
            'title': 'Test Title',
            'price': Decimal(1.5),
            'time_minutes': 20,
            'description': 'Test Description'
        }

        res = self.client.post(RECEIPE_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Testing partial field updates"""

        recipe = create_sample_recipe(self.user)
        new_title = 'New Test Title'
        original_link = recipe.link
        payload = {
            'title': new_title
        }

        res = self.client.patch(get_recipe_detail_url(recipe.id), payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, new_title)
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_no_user_update(self):
        """Testing recipe user should not get updated"""

        new_user = create_user(email='newuser@example.com')

        recipe = create_sample_recipe(user=self.user)
        payload = {'user': new_user.id}

        self.client.patch(get_recipe_detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Testing API to delete recipe"""

        recipe = create_sample_recipe(self.user)
        res = self.client.delete(get_recipe_detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe(self):
        """Testing deletion of other user's recipe"""

        new_user = create_user(email='newuser@example.com')
        recipe = create_sample_recipe(new_user)
        res = self.client.delete(get_recipe_detail_url(recipe.id))

        self.assertTrue(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Testing creation of recipe with new tags."""

        payload = {
            'title': 'Test Title',
            'price': Decimal(1.5),
            'time_minutes': 20,
            'description': 'Test Description',
            'tags': [
                {'name': 'Tag 1'},
                {'name': 'Tag 2'}
            ]
        }

        res = self.client.post(RECEIPE_URL, payload, format='json')
        print(res.data)
        recipes = Recipe.objects.filter(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipes.exists())
        self.assertEqual(recipes[0].tags.count(), len(payload['tags']))

    def test_create_recipe_with_old_tags(self):
        """Testing creation of recipe with old tags."""

        old_tag_name = 'Tag 1'
        Tag.objects.create(user=self.user, name=old_tag_name)

        payload = {
            'title': 'Test Title',
            'price': Decimal(1.5),
            'time_minutes': 20,
            'description': 'Test Description',
            'tags': [
                {'name': old_tag_name},
                {'name': 'Tag 2'}
            ]
        }

        res = self.client.post(RECEIPE_URL, payload, format='json')
        print(res.data)
        recipes = Recipe.objects.filter(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipes.exists())
        self.assertEqual(Tag.objects.filter(
            user=self.user, name=old_tag_name).count(), 1)
