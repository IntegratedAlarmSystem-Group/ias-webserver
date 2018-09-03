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
        view = View.objects.get(name="weather")
        type = Type.objects.get(name="station")
        weather_station_alarms = self.queryset.filter(
            view=view,
            type=type
        )

        data = {}
        for station_alarm in weather_station_alarms:
            nested_alarms = station_alarm.nested_alarms.all()
            data[station_alarm.placemark] = {
                "placemark": station_alarm.placemark,
                "station": station_alarm.alarm_id,
                "temperature": nested_alarms.get(
                    type=Type.objects.get(name="temperature")
                ).alarm_id,
                "windspeed": nested_alarms.get(
                    type=Type.objects.get(name="windspeed")
                ).alarm_id,
                "humidity": nested_alarms.get(
                    type=Type.objects.get(name="humidity")
                ).alarm_id,
            }

        return Response(data)

    @action(detail=False)
    def antennas_config(self, request):
        """ Retrieve the configuration used in the weather display """
        view = View.objects.get(name="antennas")
        type = Type.objects.get(name="antenna")
        antenna_alarms = self.queryset.filter(
            view=view,
            type=type
        )

        data = {}
        for alarm in antenna_alarms:
            if alarm.tags not in data:
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
        view = View.objects.get(name="summary")
        type = Type.objects.get(name="antenna")
        summary_alarm = self.queryset.get(view=view, type=type)

        return Response(summary_alarm.alarm_id)

    @action(detail=False)
    def weather_summary_config(self, request):
        """ Retrieve the configuration used in the weather summary display """
        view = View.objects.get(name="summary")
        humidity_alarm = self.queryset.get(
            view=view, type=Type.objects.get(name="humidity")
        )
        temperature_alarm = self.queryset.get(
            view=view, type=Type.objects.get(name="temperature")
        )
        windspeed_alarm = self.queryset.get(
            view=view, type=Type.objects.get(name="windspeed")
        )

        data = {
            "humidityAlarmId": humidity_alarm.alarm_id,
            "tempAlarmId": temperature_alarm.alarm_id,
            "windsAlarmId": windspeed_alarm.alarm_id
        }

        return Response(data)
