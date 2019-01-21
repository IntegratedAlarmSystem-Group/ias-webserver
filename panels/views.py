import json
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework import authentication, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from dry_rest_permissions.generics import DRYPermissions
from panels.models import (
    File, LocalAlarmConfig, AlarmConfig, View, Type, Placemark, PlacemarkGroup)
from panels.serializers import (
    AlarmConfigSerializer, PlacemarkSerializer)


logger = logging.getLogger(__name__)


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
            data = file.get_content()
            return Response(data, status=status.HTTP_200_OK)
        else:
            logger.error(
                'no file is associated to the given key %s (status %s)',
                key, status.HTTP_404_NOT_FOUND)
            return Response(
                'No file is asociated to the given key [{}]'.format(key),
                status=status.HTTP_404_NOT_FOUND
            )


class LocalAlarmConfigViewSet(viewsets.ViewSet):

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
    )

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, format=None):
        queryset = LocalAlarmConfig.objects.all()
        data = [e.to_dict() for e in queryset]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False)
    def get_json(self, request):
        key = request.GET.get('key', None)
        file = File.objects.get_instance_for_localfile(key)
        isAvailable = (file is not None)
        if isAvailable:
            isConfigFile = file.is_config_file()
            if isConfigFile:
                data = file.get_content()
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


class AlarmConfigViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""

    queryset = AlarmConfig.objects.all()
    views = View.objects.all()
    types = Type.objects.all()
    serializer_class = AlarmConfigSerializer
    permission_classes = (DRYPermissions,)

    @action(detail=False)
    def weather_config(self, request):
        """ Retrieve the configuration used in the weather display """

        weather_station_alarms = self.queryset.filter(
            view__name="weather",
            type__name="station"
        )
        if not len(weather_station_alarms):
            logger.warning(
                'there is no configuration for alarms in weather display'
            )
            return Response(
                'There is no configuration for weather display',
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for alarm in weather_station_alarms:
            children = []

            for sub_alarm in alarm.nested_alarms.all():
                mark = sub_alarm.placemark.name if sub_alarm.placemark else ""
                children.append({
                  "alarm_id": sub_alarm.alarm_id,
                  "custom_name": sub_alarm.custom_name,
                  "type": sub_alarm.type.name,
                  "view": sub_alarm.view.name,
                  "placemark": mark,
                  "group": alarm.placemark.group.name,
                  "children": []
                })

            data.append(
                {
                  "alarm_id": alarm.alarm_id,
                  "custom_name": alarm.custom_name,
                  "type": alarm.type.name,
                  "view": alarm.view.name,
                  "placemark": alarm.placemark.name if alarm.placemark else "",
                  "group": alarm.placemark.group.name,
                  "children": children
                }
            )

        return Response(data)

    @action(detail=False)
    def antennas_config(self, request):
        """ Retrieve the configuration used in the weather display """

        antenna_alarms = self.queryset.filter(
            view__name="antennas",
            type__name="antenna"
        )
        if not len(antenna_alarms):
            logger.warning(
                'there is no configuration for antennas display'
            )
            return Response(
                'There is no configuration for antennas display',
                status=status.HTTP_404_NOT_FOUND
            )

        data = {}
        data["antennas"] = []
        for alarm in antenna_alarms:
            children = []

            for sub_alarm in alarm.nested_alarms.all():
                mark = sub_alarm.placemark.name if sub_alarm.placemark else ""
                children.append({
                  "alarm_id": sub_alarm.alarm_id,
                  "custom_name": sub_alarm.custom_name,
                  "type": sub_alarm.type.name,
                  "view": sub_alarm.view.name,
                  "placemark": mark,
                  "group": "antennas",
                  "children": []
                })

            data["antennas"].append(
                {
                  "alarm_id": alarm.alarm_id,
                  "custom_name": alarm.custom_name,
                  "type": alarm.type.name,
                  "view": alarm.view.name,
                  "placemark": alarm.placemark.name if alarm.placemark else "",
                  "group": "antennas",
                  "children": children
                }
            )

        other_devices = self.queryset.filter(
            view__name="antennas",
            type__name="device"
        )
        if not len(other_devices):
            logger.warning(
                'there is no configuration for other array devices'
            )
            return Response(data)

        data["devices"] = []
        for alarm in other_devices:
            data["devices"].append(
                {
                  "alarm_id": alarm.alarm_id,
                  "custom_name": alarm.custom_name,
                  "type": alarm.type.name,
                  "view": alarm.view.name,
                  "placemark": alarm.placemark.name if alarm.placemark else "",
                  "group": "global_devices",
                  "children": []
                }
            )

        return Response(data)

    @action(detail=False)
    def antennas_summary_config(self, request):
        """ Retrieve the configuration used in the antennas summary display """

        summary_alarm = self.queryset.filter(
            view__name="summary",
            type__name="antenna"
        )

        if not summary_alarm:
            logger.warning(
                'there is no configuration for antennas summary (main view)'
            )
            return Response(
                'There is no configuration for antennas summary',
                status=status.HTTP_404_NOT_FOUND
            )
        data = [{
            'alarm_id': summary_alarm[0].alarm_id,
            'custom_name': 'Antennas',
            'type': summary_alarm[0].type.name,
            'view': summary_alarm[0].view.name,
            'children': [],
            'placemark': '',
            'group': '',
        }]

        return Response(data)

    @action(detail=False)
    def weather_summary_config(self, request):
        """ Retrieve the configuration used in the weather summary display """

        data = []
        configuration_available = False

        humidity_alarm = self.queryset.filter(
            view__name="summary", type__name="humidity"
        )
        if humidity_alarm:
            data.append(
                {
                    'alarm_id': humidity_alarm[0].alarm_id,
                    'custom_name': 'Humidity',
                    'type': 'humidity',
                    'view': 'weather_summary',
                    'placemark': '',
                    'group': '',
                    'children': [],
                },
            )
            configuration_available = True

        temperature_alarm = self.queryset.filter(
            view__name="summary", type__name="temperature"
        )
        if temperature_alarm:
            data.append(
                {
                    'alarm_id': temperature_alarm[0].alarm_id,
                    'custom_name': 'Temperature',
                    'type': 'temperature',
                    'view': 'weather_summary',
                    'placemark': '',
                    'group': '',
                    'children': [],
                },
            )
            configuration_available = True

        windspeed_alarm = self.queryset.filter(
            view__name="summary", type__name="windspeed"
        )
        if windspeed_alarm:
            data.append(
                {
                    'alarm_id': windspeed_alarm[0].alarm_id,
                    'custom_name': 'Wind Speed',
                    'type': 'windspeed',
                    'view': 'weather_summary',
                    'placemark': '',
                    'group': '',
                    'children': [],
                },
            )
            configuration_available = True

        if configuration_available:
            return Response(data)
        else:
            logger.warning(
                'there is no configuration for weather summary (main view)'
            )
            return Response(
                'There is no configuration for weather summary alarms',
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False)
    def ias_health_summary_config(self, request):
        """ Retrieve the configuration used in the antennas summary display """

        summary_alarm = self.queryset.filter(
            view__name="summary",
            type__name="health"
        )

        if not summary_alarm:
            logger.warning(
                'there is no configuration for ias health summary (main view)'
            )
            return Response(
                'There is no configuration for ias health summary',
                status=status.HTTP_404_NOT_FOUND
            )

        data = [{
            'alarm_id': summary_alarm[0].alarm_id,
            'custom_name': 'IAS',
            'type': summary_alarm[0].type.name,
            'view': summary_alarm[0].view.name,
            'children': [],
            'placemark': '',
            'group': '',
        }]

        return Response(data)


class PlacemarkViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""

    queryset = Placemark.objects.all()
    groups = PlacemarkGroup.objects.all()
    serializer_class = PlacemarkSerializer
    permission_classes = (DRYPermissions,)

    @action(detail=False)
    def pads_by_group(self, request):
        """ Retrieve the list of pads and their associated antenna by group """
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
        pads = self.queryset.filter(type__name="pad")
        if group_name:
            response[group_name] = {}
            member_pads = pads.filter(group__name=group_name)
            for pad in member_pads:
                antenna = None
                if hasattr(pad, 'alarm'):
                    antenna = pad.alarm.custom_name
                response[group_name][pad.name] = antenna

        else:
            for pad in pads:
                antenna = None
                if hasattr(pad, 'alarm'):
                    antenna = pad.alarm.custom_name
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
