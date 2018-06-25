from rest_framework import serializers
from tickets.models import Ticket, ShelveRegistry


class TicketSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Ticket
        fields = '__all__'


class ShelveRegistrySerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = ShelveRegistry
        fields = '__all__'
