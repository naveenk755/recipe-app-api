from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of IDs to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Commad separated list of IDs to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipe APIs."""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert comma separated values to list of int"""

        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Apply filters to query set based on query params"""

        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        query_set = self.queryset

        if tags:
            tag_ids = self._params_to_ints(tags)
            query_set = query_set.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            query_set = query_set.filter(ingredients__id__in=ingredient_ids)

        return query_set.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        """Returns the serializer class for the request."""

        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""

        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.ListModelMixin,
                            mixins.DestroyModelMixin):
    """Base view set for Recipe attribute viewsets"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseRecipeAttrViewSet):
    """View for managing tag APIs."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredientViewSet(BaseRecipeAttrViewSet):
    """View for managing ingredient APIs"""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')
