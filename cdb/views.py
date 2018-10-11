from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from cdb.readers import CdbReader


@api_view(['LIST', 'GET'])
def retrieve_ias(request, pk=None, format=None):
    data = CdbReader.read_ias()
    return Response(data, status=status.HTTP_200_OK)
