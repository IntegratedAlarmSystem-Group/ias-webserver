from rest_framework import serializers
from panels.models import Placemark


class PlacemarkSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Placemark
        fields = '__all__'
