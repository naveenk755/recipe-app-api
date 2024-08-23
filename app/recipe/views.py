from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipe APIs."""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')

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
