from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
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

    @action(detail=False)
    def old_open_info(self, request):
        """ Retrieve a dictionary with information of the open tickets related
        with an alarm and its dependencies """
        alarm_id = self.request.query_params.get('alarm_id', None)
        data = {}
        if(alarm_id):
            all_alarms_ids = AlarmConnector.get_alarm_dependencies(alarm_id)
            for alarm_id in all_alarms_ids:
                queryset = Ticket.objects.filter(
                    alarm_id=alarm_id,
                    status=TicketStatus.get_choices_by_name()['CLEARED_UNACK']
                )
                data[alarm_id] = [ticket.pk for ticket in queryset]

        return Response(data)

    @action(methods=['put'], detail=False)
    def acknowledge(self, request):
        """ Acknowledge multiple tickets with the same message and timestamp"""
        message = self.request.data['message']
        alarms_ids = self.request.data['alarms_ids']

        # If empty Message then return Bad Request:
        if message.strip() is "":
            return Response(
                "The message must not be empty",
                status=status.HTTP_400_BAD_REQUEST
            )

        ack_alarms_ids = AlarmConnector.acknowledge_alarms(alarms_ids)
        queryset = Ticket.objects.filter(alarm_id__in=ack_alarms_ids)

        # possible unack states
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']

        queryset = queryset.filter(
            status__in=[int(unack), int(cleared_unack)]
        )

        return self._apply_acknowledgement(message, list(queryset))

    def _apply_acknowledgement(self, message, tickets):
        """ Applies the acknowledgement to a single or multiple tickets """
        # Acknowledge each ticket:
        ack_alarms = set()
        for ticket in tickets:
            response = ticket.acknowledge(message=message)
            if response == 'solved':
                ack_alarms.add(ticket.alarm_id)
            else:
                return Response(
                    'Unexpected response from a ticket acknowledgement',
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                # TODO: Reset AlarmCollection (?)
        return Response(list(ack_alarms), status=status.HTTP_200_OK)


class ShelveRegistryViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` ShelveRegistries"""
    queryset = ShelveRegistry.objects.all()
    serializer_class = ShelveRegistrySerializer

    def create(self, request, *args, **kwargs):
        """ Redefine create method in order to notify to the alarms app """
        response = super(ShelveRegistryViewSet, self).create(
            request, *args, **kwargs
        )
        if response.status_code == status.HTTP_201_CREATED:
            AlarmConnector.shelve_alarm(response.data['alarm_id'])
        return response

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

    @action(methods=['put'], detail=False)
    def unshelve(self, request):
        """ Unshelve multiple registries """
        alarms_ids = self.request.data['alarms_ids']

        # TODO: Move this to a classmethod and here only call it
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
        AlarmConnector.unshelve_alarms(alarms_to_unshelve)
        return Response(alarms_to_unshelve, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False)
    def check_timeouts(self, request):
        """ Check if the timeouts of the registries are reached """
        print('Checking Shelved Alarms timeouts')
        # TODO: Move this to a classmethod and here call that method
        registries_to_unshelve = []
        registries = ShelveRegistry.objects.filter(
            status=ShelveRegistryStatus.get_choices_by_name()['SHELVED']
        )
        for registry in registries:
            if(registry.shelved_at + registry.timeout <= timezone.now()):
                registries_to_unshelve.append(registry)
        return self._apply_unshelving(registries_to_unshelve)
