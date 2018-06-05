from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from cdb.models import Iasio, Ias
from cdb.serializers import (
    IasioSerializer, IasSerializer
)


class IasViewSet(viewsets.ModelViewSet):
    """ Provides API to perform the following actions in the Ias table:
    `List`, `Create`, `Retrieve`, `Update` and `Destroy`."""
    queryset = Ias.objects.all()
    serializer_class = IasSerializer


class IasioViewSet(viewsets.ModelViewSet):
    """ Provides API to perform the following actions in the Iasio table:
    `List`, `Create`, `Retrieve`, `Update` and `Destroy`."""
    queryset = Iasio.objects.all()
    serializer_class = IasioSerializer

    @action(detail=False)
    def filtered_by_alarm(self, request):
        """ Retrieve the list of iasios filtered by type alarm """
        alarm_iasios = Iasio.objects.filter(ias_type='ALARM')
        serializer = self.get_serializer(alarm_iasios, many=True)
        return Response(serializer.data)
