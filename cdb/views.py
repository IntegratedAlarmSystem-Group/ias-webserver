from rest_framework import viewsets
from cdb.models import Iasio, Ias
from cdb.serializers import (
    IasioSerializer, IasSerializer
)


class IasViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Ias."""
    queryset = Ias.objects.all()
    serializer_class = IasSerializer


class IasioViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Iasio."""
    queryset = Iasio.objects.all()
    serializer_class = IasioSerializer
