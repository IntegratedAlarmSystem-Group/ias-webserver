import json
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from panels.models import File
from panels.serializers import FileSerializer


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
