from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model

from core.models import Recipe, Tag, Ingredient

from decimal import Decimal
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

import tempfile
import os
from PIL import Image

RECEIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_user(email='test@example.com', password='testpasswoed'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


def get_recipe_detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_sample_recipe(user, **params) -> Tag:
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
        recipes = Recipe.objects.filter(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipes.exists())
        self.assertEqual(Tag.objects.filter(
            user=self.user, name=old_tag_name).count(), 1)

    def test_update_tag_to_recipe(self):
        """Testing update new tags to existing recipe."""

        new_tag_name = 'lunch'
        recipe = create_sample_recipe(user=self.user)
        payload = {'tags': [{'name': new_tag_name}]}

        res = self.client.patch(get_recipe_detail_url(
            recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        final_tags = recipe.tags.all()
        self.assertEqual(final_tags.count(), 1)
        self.assertEqual(final_tags[0].name, new_tag_name)

    def test_update_tags_list(self):
        """Tesing list update on pushing new tag list"""

        recipe = create_sample_recipe(self.user)
        old_name = 'test tag'
        old_tag = Tag.objects.create(user=self.user, name=old_name)
        recipe.tags.add(old_tag)

        new_tag_name = 'test tag'
        payload = {'tags': [{
            'name': new_tag_name
        }]}

        res = self.client.patch(get_recipe_detail_url(
            recipe.id), payload, format='json')

        final_tags = recipe.tags.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(final_tags.count(), 1)
        self.assertEqual(final_tags[0].name, new_tag_name)

    def test_clear_tag(self):
        """Testing clearing of tags"""

        recipe = create_sample_recipe(user=self.user)
        old_name = 'test tag'
        old_tag = Tag.objects.create(user=self.user, name=old_name)
        recipe.tags.add(old_tag)

        payload = {'tags': []}

        res = self.client.patch(get_recipe_detail_url(
            recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.all().count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Tetsing creating recipe with new ingredients"""

        payload = {
            'title': 'Test Title',
            'price': Decimal(1.5),
            'time_minutes': 20,
            'description': 'Test Description',
            'ingredients': [
                {'name': 'Ingredient 1'},
                {'name': 'Ingredient 2'}
            ]
        }

        res = self.client.post(RECEIPE_URL, payload, format='json')
        recipes = Recipe.objects.filter(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipes.exists())
        self.assertEqual(recipes[0].ingredients.count(),
                         len(payload['ingredients']))

    def test_create_recipe_with_existing_ingredients(self):
        """Testing creating recipe with existing ingredients."""

        existing_ingredient_name = 'ingredient 1'
        Ingredient.objects.create(
            user=self.user, name=existing_ingredient_name)
        payload = {
            'title': 'Test Title',
            'price': Decimal(1.5),
            'time_minutes': 20,
            'description': 'Test Description',
            'ingredients': [
                {'name': 'Ingredient 1'},
                {'name': existing_ingredient_name}
            ]
        }

        res = self.client.post(RECEIPE_URL, payload, format='json')
        recipes = Recipe.objects.filter(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(recipes.exists())
        self.assertEqual(Ingredient.objects.filter(
            name=existing_ingredient_name,
            user=self.user
        ).count(), 1)

    def test_adding_ingredient_to_recipe(self):
        """Testing adding ingredient list to recipe"""

        recipe = create_sample_recipe(user=self.user)
        payload = {
            'ingredients': [
                {'name': 'Ingredient1'},
                {'name': 'Ingredient2'}
            ]
        }

        url = get_recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertTrue(recipe.ingredients.all().count(), 2)

    def test_updating_ingredients_to_recipe(self):
        """Testing updating the ingredient list in recipe."""

        existing_ingredient = 'OLD INGREDIENT'
        new_ingredient = 'NEW INGREDIENT'
        recipe = create_sample_recipe(user=self.user)
        ing1 = Ingredient.objects.create(
            user=self.user, name=existing_ingredient)
        recipe.ingredients.add(ing1)

        payload = {
            'ingredients': [
                {'name': new_ingredient}
            ]
        }

        url = get_recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        final_recipes = recipe.ingredients.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(final_recipes.count(), 1)
        self.assertEqual(final_recipes[0].name, new_ingredient)


class ImageUploadTests(TestCase):
    """Testing image upload functionality"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.recipe = create_sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Testing recipe image upload"""

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = dict(image=image_file)
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(os.path.exists(self.recipe.image.path))
