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

            data.append({
                "placemark": station_alarm.placemark,
                "station": station_alarm.alarm_id,
                "temperature": temperature[0].alarm_id if temperature else "",
                "windspeed": windspeed[0].alarm_id if windspeed else "",
                "humidity": humidity[0].alarm_id if humidity else ""
            })

        return Response(data)

    @action(detail=False)
    def antennas_config(self, request):
        """ Retrieve the configuration used in the weather display """

        try:
            view = View.objects.get(name="antennas")
        except View.DoesNotExist:
            return Response(
                'There is no configuration for antennas displays',
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            type = Type.objects.get(name="antenna")
        except Type.DoesNotExist:
            return Response(
                'There is no configuration for antennas alarms',
                status=status.HTTP_404_NOT_FOUND
            )

        antenna_alarms = self.queryset.filter(
            view=view,
            type=type
        )

        data = {}
        for alarm in antenna_alarms:
            if alarm.tags and alarm.tags not in data:
                data[alarm.tags] = []
            data[alarm.tags].append(
                {
                  "antenna": alarm.custom_name,
                  "placemark": alarm.placemark,
                  "alarm": alarm.alarm_id,
                }
            )

        return Response(data)

    @action(detail=False)
    def antennas_summary_config(self, request):
        """ Retrieve the configuration used in the antennas summary display """
        try:
            view = View.objects.get(name="summary")
        except View.DoesNotExist:
            return Response(
                'There is no configuration for summary displays',
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            type = Type.objects.get(name="antenna")
        except Type.DoesNotExist:
            return Response(
                'There is no configuration for antennas alarms',
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            summary_alarm = self.queryset.get(view=view, type=type)
            response = summary_alarm.alarm_id
            return Response(response)
        except AlarmConfig.DoesNotExist:
            return Response(
                'There is no configuration for antennas summary',
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False)
    def weather_summary_config(self, request):
        """ Retrieve the configuration used in the weather summary display """
        try:
            view = View.objects.get(name="summary")
        except View.DoesNotExist:
            return Response(
                'There is no configuration for summary displays',
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            humidity_type = Type.objects.get(name="humidity")
        except Type.DoesNotExist:
            return Response(
                'There is no configuration for himidity alarms',
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            temperature_type = Type.objects.get(name="temperature")
        except Type.DoesNotExist:
            return Response(
                'There is no configuration for temperature alarms',
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            windspeed_type = Type.objects.get(name="windspeed")
        except Type.DoesNotExist:
            return Response(
                'There is no configuration for windspeed alarms',
                status=status.HTTP_404_NOT_FOUND
            )

        data = {}
        configuration_available = False

        try:
            humidity_alarm = self.queryset.get(
                view=view, type=humidity_type
            )
            data["humidity"] = humidity_alarm.alarm_id
            configuration_available = True
        except AlarmConfig.DoesNotExist:
            data["humidity"] = ""

        try:
            temperature_alarm = self.queryset.get(
                view=view, type=temperature_type
            )
            data["temperature"] = temperature_alarm.alarm_id
            configuration_available = True
        except AlarmConfig.DoesNotExist:
            data["temperature"] = ""

        try:
            windspeed_alarm = self.queryset.get(
                view=view, type=windspeed_type
            )
            data["windspeed"] = windspeed_alarm.alarm_id
            configuration_available = True
        except AlarmConfig.DoesNotExist:
            data["windspeed"] = ""

        if configuration_available:
            return Response(data)
        else:
            return Response(
                'There is no configuration for weather summary alarms',
                status=status.HTTP_404_NOT_FOUND
            )
