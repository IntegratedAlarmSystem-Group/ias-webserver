from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from tickets.connectors import AlarmConnector
from tickets.models import (
    Ticket, TicketStatus,
    ShelveRegistry,
    ShelveRegistryStatus
)
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

    @action(methods=['put'], detail=False)
    def acknowledge(self, request):
        """ Acknowledge multiple tickets with the same message and timestamp"""
        message = self.request.data['message']
        alarms_ids = self.request.data['alarms_ids']
        filter = 'only-set'
        if 'filter' in self.request.data:
            filter = self.request.data['filter']

        queryset = Ticket.objects.filter(alarm_id__in=alarms_ids)

        # possible unack states
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']

        if filter and filter == 'only-cleared':
            queryset = queryset.filter(
                status=int(cleared_unack)
            )
        elif filter and filter == 'all':
            queryset = queryset.filter(
                status__in=[int(unack), int(cleared_unack)]
            )
        elif (filter and filter == 'only-set') or not filter:
            queryset = queryset.filter(
                status=int(unack)
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
        alarms_to_ack = set()
        for ticket in tickets:
            response = ticket.acknowledge(message=message)
            if response == 'solved':
                alarms_to_ack.add(ticket.alarm_id)
            else:
                return Response(
                    'Unexpected response from a ticket acknowledgement',
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        list_of_alarms_to_ack = self._verify_acknowledge_alarms(
            list(alarms_to_ack))
        if list_of_alarms_to_ack:
            AlarmConnector.acknowledge_alarms(list_of_alarms_to_ack)
        return Response(list_of_alarms_to_ack, status=status.HTTP_200_OK)

    def _verify_acknowledge_alarms(self, alarms_to_ack):
        """Check the alarms list to build a new list that contains only the
        alarms that have only ack or cleared_ack tickets"""
        # possible unack states
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']
        completly_ack_alarms = []
        for alarm_id in alarms_to_ack:
            queryset = Ticket.objects.filter(alarm_id=alarm_id)
            queryset = queryset.filter(
                status__in=[int(unack), int(cleared_unack)]
            )
            if not queryset:
                completly_ack_alarms.append(alarm_id)
        return completly_ack_alarms


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

    @action(methods=['put'], detail=True)
    def unshelve(self, request, pk=None):
        """ Unshelve a registry that implies change the status,
        record message an the timestamp """
        registry = ShelveRegistry.objects.filter(pk=pk).first()

        if not registry:
            return Response(
                "The registry does not exist",
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(registry.unshelve(), status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False)
    def unshelve_many(self, request):
        """ Unshelve multiple registries """
        alarms_ids = self.request.data['alarms_ids']

        queryset = ShelveRegistry.objects.filter(alarm_id__in=alarms_ids)
        queryset = queryset.filter(
            status=int(ShelveRegistryStatus.get_choices_by_name()['SHELVED'])
        )
        return self._apply_unshelving(list(queryset))

    def _apply_unshelving(self, registries):
        """ Applies the unshelving to a single or multiple registries """
        # Handle either single or multiple registries:
        if type(registries) is not list:
            registries = [registries]
        # Unshelve each registry:
        alarms_to_unshelve = []
        for registry in registries:
            response = registry.unshelve()
            if response == 'unshelved':
                alarms_to_unshelve.append(registry.alarm_id)
            else:
                return Response(
                    'Unexpected response from a registry unshelving',
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(alarms_to_unshelve, status=status.HTTP_200_OK)
