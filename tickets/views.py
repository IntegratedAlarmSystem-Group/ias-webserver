from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from tickets.models import Ticket
from tickets.serializers import (
    TicketSerializer
)


class TicketViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Ias."""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    @action(detail=False)
    def filters(self, request):
        """ Retrieve the list of iasios filtered by type alarm """
        alarm_id = self.request.query_params.get('alarm_id', None)
        status = self.request.query_params.get('status', None)
        queryset = Ticket.objects.all()
        if alarm_id:
            queryset = queryset.filter(alarm_id=alarm_id)
        if status:
            queryset = queryset.filter(status=status)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def resolve(self, request, pk=None):
        """ Resolve a ticket that implies change the status, record message an
        the timestamp """
        message = self.request.data['message']
        ticket = Ticket.objects.filter(pk=pk).first()

        if ticket:
            response = ticket.resolve(message=message)
            if response == 'solved':
                return Response("The ticket was solved")
            elif response == 'ignored-wrong-message':
                return Response("The message must not be empty",
                                status=status.HTTP_400_BAD_REQUEST)
            elif response == 'ignored-ticket-closed':
                return Response("The message is already closed",
                                status=status.HTTP_400_BAD_REQUEST)
        return Response("The ticket does not exist",
                        status=status.HTTP_404_NOT_FOUND)
