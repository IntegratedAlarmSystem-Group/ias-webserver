import json
import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from dry_rest_permissions.generics import DRYPermissions
from panels.models import (
    File, AlarmConfig, View, Type, Placemark, PlacemarkGroup)
from panels.serializers import (
    FileSerializer, AlarmConfigSerializer, PlacemarkSerializer)

logger = logging.getLogger(__name__)


class FileViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""

    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (DRYPermissions,)

    @action(detail=False)
    def get_json(self, request):
        """ Retrieve the list of tickets filtered by alarm and status """
        key = request.query_params.get('key')
        try:
            file = File.objects.get(key=key)
        except ObjectDoesNotExist:
            logger.error(
                'no file is associated to the given key %s (status %s)',
                key, status.HTTP_404_NOT_FOUND)
            return Response(
                'No file is asociated to the given key ' + key,
                status=status.HTTP_404_NOT_FOUND
            )
        url = file.get_full_url()
        with open(url) as f:
            data = json.load(f)
        return Response(data)


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

            temperature = alarm.nested_alarms.filter(
                type__name="temperature")

            windspeed = alarm.nested_alarms.filter(
                type__name="windspeed")

            humidity = alarm.nested_alarms.filter(
                type__name="humidity")

            group_name = ""
            if alarm.placemark and alarm.placemark.group:
                group_name = alarm.placemark.group.name
            data.append({
                "placemark": alarm.placemark.name if alarm.placemark else "",
                "group": group_name,
                "station": alarm.alarm_id,
                "temperature": temperature[0].alarm_id if temperature else "",
                "windspeed": windspeed[0].alarm_id if windspeed else "",
                "humidity": humidity[0].alarm_id if humidity else ""
            })

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
        for alarm in antenna_alarms:
            fire = alarm.nested_alarms.filter(
                type__name="fire")

            fire_sys = alarm.nested_alarms.filter(
                type__name="fire_malfunction")

            ups = alarm.nested_alarms.filter(
                type__name="ups")

            hvac = alarm.nested_alarms.filter(
                type__name="hvac")

            power = alarm.nested_alarms.filter(
                type__name="power")

            if alarm.tags and alarm.tags not in data:
                data[alarm.tags] = []
            data[alarm.tags].append(
                {
                  "antenna": alarm.custom_name,
                  "placemark": alarm.placemark.name if alarm.placemark else "",
                  "alarm": alarm.alarm_id,
                  "fire": fire[0].alarm_id if fire else "",
                  "fire_malfunction": fire_sys[0].alarm_id if fire_sys else "",
                  "ups": ups[0].alarm_id if ups else "",
                  "hvac": hvac[0].alarm_id if hvac else "",
                  "power": power[0].alarm_id if power else ""
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

        return Response(summary_alarm[0].alarm_id)

    @action(detail=False)
    def weather_summary_config(self, request):
        """ Retrieve the configuration used in the weather summary display """

        data = {
            "placemark": "",
            "station": "",
            "humidity": "",
            "temperature": "",
            "windspeed": ""
        }
        configuration_available = False

        humidity_alarm = self.queryset.filter(
            view__name="summary", type__name="humidity"
        )
        if humidity_alarm:
            data["humidity"] = humidity_alarm[0].alarm_id
            configuration_available = True

        temperature_alarm = self.queryset.filter(
            view__name="summary", type__name="temperature"
        )
        if temperature_alarm:
            data["temperature"] = temperature_alarm[0].alarm_id
            configuration_available = True

        windspeed_alarm = self.queryset.filter(
            view__name="summary", type__name="windspeed"
        )
        if windspeed_alarm:
            data["windspeed"] = windspeed_alarm[0].alarm_id
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

        return Response(summary_alarm[0].alarm_id)


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
