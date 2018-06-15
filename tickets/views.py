from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from tickets.models import Ticket, TicketStatus, ShelveRegistry
from tickets.connectors import AlarmConnector
from tickets.serializers import (
    TicketSerializer,
    ShelveRegistrySerializer,
)


class TicketViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Tickets."""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    @action(detail=False)
    def filters(self, request):
        """ Retrieve the list of tickets filtered by alarm and status """
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
    def acknowledge(self, request, pk=None):
        """ Acknowledge a ticket that implies change the status,
        record message an the timestamp """
        message = self.request.data['message']
        ticket = Ticket.objects.filter(pk=pk).first()

        if not ticket:
            return Response(
                "The ticket does not exist",
                status=status.HTTP_404_NOT_FOUND
            )
        return self._apply_acknowledgement(message, ticket)

    @action(methods=['put'], detail=False)
    def acknowledge_many(self, request):
        """ Acknowledge multiple tickets with the same message and timestamp"""
        message = self.request.data['message']
        alarms_ids = self.request.data['alarms_ids']

        queryset = Ticket.objects.filter(alarm_id__in=alarms_ids)
        queryset = queryset.filter(
            status=int(TicketStatus.get_choices_by_name()['UNACK'])
        )
        return self._apply_acknowledgement(message, list(queryset))

    def _apply_acknowledgement(self, message, tickets):
        """ Applies the acknowledgement to a single or multiple tickets """
        # If empty Message then return Bad Request:
        if message.strip() is "":
            return Response(
                "The message must not be empty",
                status=status.HTTP_400_BAD_REQUEST
            )
        # Handle either single or multiple tickets:
        if type(tickets) is not list:
            tickets = [tickets]
        # Acknowledge each ticket:
        alarms_to_ack = []
        for ticket in tickets:
            response = ticket.acknowledge(message=message)
            if response == 'solved':
                alarms_to_ack.append(ticket.alarm_id)
            else:
                return Response(
                    'Unexpected response from a ticket acknowledgement',
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        AlarmConnector.acknowledge_alarms(alarms_to_ack)
        return Response(alarms_to_ack, status=status.HTTP_200_OK)


class ShelveRegistryViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` ShelveRegistries"""
    queryset = ShelveRegistry.objects.all()
    serializer_class = ShelveRegistrySerializer

    @action(detail=False)
    def filters(self, request):
        """ Retrieve the list of tickets filtered by alarm and status """
        alarm_id = self.request.query_params.get('alarm_id', None)
        status = self.request.query_params.get('status', None)
        queryset = ShelveRegistry.objects.all()
        if alarm_id:
            queryset = queryset.filter(alarm_id=alarm_id)
        if status:
            queryset = queryset.filter(status=status)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
