from rest_framework import serializers
from ias_webserver.settings import BROADCAST_RATE_FACTOR
from cdb.models import Ias, Iasio


class IasSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    broadcast_factor = serializers.SerializerMethodField()

    def get_broadcast_factor(self, ias):
        return BROADCAST_RATE_FACTOR

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Ias
        fields = '__all__'


class IasioSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Iasio
        fields = '__all__'
