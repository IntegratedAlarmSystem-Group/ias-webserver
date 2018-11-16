import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from users.serializers import (
    UserSerializer
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Tickets."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that the view requires
        """
        if self.action == 'filter':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False)
    def filter(self, request):
        """ Retrieve the list of users filtered by group """
        group = self.request.query_params.get('group', None)
        queryset = User.objects.all()
        if group:
            queryset = queryset.filter(groups__name=group)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
