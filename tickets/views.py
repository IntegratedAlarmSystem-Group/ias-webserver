from rest_framework import viewsets
from tickets.models import Ticket
from tickets.serializers import (
    TicketSerializer
)


class TicketViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Ias."""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
