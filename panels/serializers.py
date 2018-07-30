from rest_framework import serializers
from panels.models import File


class FileSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = File
        fields = '__all__'
