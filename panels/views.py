from django.shortcuts import render
from rest_framework import viewsets, status
from panels.models import File
from panels.serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Files."""
    queryset = File.objects.all()
    serializer_class = FileSerializer
