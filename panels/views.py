import json
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from panels.models import File, AlarmConfig, View, Type
from panels.serializers import FileSerializer, AlarmConfigSerializer


class FileViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""

    queryset = File.objects.all()
    serializer_class = FileSerializer

    @action(detail=False)
    def get_json(self, request):
        """ Retrieve the list of tickets filtered by alarm and status """
        key = request.query_params.get('key')
        try:
            file = File.objects.get(key=key)
        except ObjectDoesNotExist:
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

    @action(detail=False)
    def weather_config(self, request):
        """ Retrieve the configuration used in the weather display """

        weather_station_alarms = self.queryset.filter(
            view__name="weather",
            type__name="station"
        )
        if not len(weather_station_alarms):
            return Response(
                'There is no configuration for weather display',
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for station_alarm in weather_station_alarms:

            temperature = station_alarm.nested_alarms.filter(
                type__name="temperature")

            windspeed = station_alarm.nested_alarms.filter(
                type__name="windspeed")

            humidity = station_alarm.nested_alarms.filter(
                type__name="humidity")

            p = station_alarm.placemark.name if station_alarm.placemark else ""
            data.append({
                "placemark": p,
                "station": station_alarm.alarm_id,
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
            return Response(
                'There is no configuration for weather summary alarms',
                status=status.HTTP_404_NOT_FOUND
            )
