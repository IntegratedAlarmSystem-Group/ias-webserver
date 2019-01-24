import logging
from rest_framework import viewsets, status
from rest_framework import authentication, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from dry_rest_permissions.generics import DRYPermissions
from panels.models import (
    File, AlarmConfig, Placemark, PlacemarkGroup)
from panels.serializers import PlacemarkSerializer
from panels.connectors import ValueConnector

logger = logging.getLogger(__name__)

ANTENNAS_CONFIG_FILE_KEY = 'antennas_config'


class FileViewSet(viewsets.ViewSet):

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
    )

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, format=None):
        queryset = File.objects.all()
        data = [f.to_dict() for f in queryset]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False)
    def get_json(self, request):
        key = request.GET.get('key', None)
        file = File.objects.get_instance_for_localfile(key)
        isAvailable = (file is not None)
        if isAvailable:
            data = file.get_content_data()
            return Response(data, status=status.HTTP_200_OK)
        else:
            logger.error(
                'no file is associated to the given key %s (status %s)',
                key, status.HTTP_404_NOT_FOUND)
            return Response(
                'No file is asociated to the given key [{}]'.format(key),
                status=status.HTTP_404_NOT_FOUND
            )


class AlarmConfigViewSet(viewsets.ViewSet):

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
    )

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, format=None):
        queryset = AlarmConfig.objects.all()
        data = [e.to_dict() for e in queryset]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False)
    def get_json(self, request):
        key = request.GET.get('key', None)
        if key == ANTENNAS_CONFIG_FILE_KEY:
            values = ValueConnector.get_antennas_to_pad_values()
            data = AlarmConfig.objects.get_file_configuration_data(
                key, update_placemark_values=values)
        else:
            data = AlarmConfig.objects.get_file_configuration_data(key)
        if data is not None:
            return Response(data, status=status.HTTP_200_OK)
        else:
            logger.error(
                "no configuration file is associated "
                "to the given key %s (status %s)",
                key, status.HTTP_404_NOT_FOUND)
            return Response(
                "No configuration file is asociated "
                "to the given key [{}]".format(key),
                status=status.HTTP_404_NOT_FOUND
            )


class PlacemarkViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""

    queryset = Placemark.objects.all()
    groups = PlacemarkGroup.objects.all()
    serializer_class = PlacemarkSerializer
    permission_classes = (DRYPermissions,)

    @action(detail=False)
    def pads_by_group(self, request):
        """ Retrieve the list of pads and their associated antenna by group """

        def get_placemark_to_alarm_config_dict():
            key = ANTENNAS_CONFIG_FILE_KEY
            values = ValueConnector.get_antennas_to_pad_values()
            a_configs = AlarmConfig.objects.get_file_configurations(
                key, update_placemark_values=values)
            placemark_to_alarm_config = {
                c.placemark:
                c for c in a_configs if c.placemark.strip() is not ""}
            return placemark_to_alarm_config

        group_name = self.request.query_params.get('group', None)
        group = self.groups.filter(name=group_name).first()
        if group_name and not group:
            logger.warning(
                'there is no pad group with the given name %s', group_name
            )
            return Response(
                'There is no group with the given name',
                status=status.HTTP_404_NOT_FOUND
            )
        response = {}
        placemark_to_alarm_config = get_placemark_to_alarm_config_dict()
        pads = self.queryset.filter(type__name="pad")
        if group_name:
            response[group_name] = {}
            member_pads = pads.filter(group__name=group_name)
            for pad in member_pads:
                antenna = None
                if pad.name in placemark_to_alarm_config:
                    antenna = placemark_to_alarm_config[pad.name].custom_name
                response[group_name][pad.name] = antenna
        else:
            for pad in pads:
                antenna = None
                if pad.name in placemark_to_alarm_config:
                    antenna = placemark_to_alarm_config[pad.name].custom_name
                group = pad.group.name if pad.group else None
                if group:
                    if group not in response:
                        response[group] = {}
                    response[group][pad.name] = antenna
                else:
                    if 'other' not in response:
                        response['other'] = {}
                    response['other'][pad.name] = antenna

        return Response(response)
