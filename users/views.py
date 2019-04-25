import logging
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from users.serializers import UserSerializer, LoginUserSerializer

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """`List`, `Create`, `Retrieve`, `Update` and `Destroy` Users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that the view requires
        """
        if self.action in [
            'filter',
            'can_ack',
            'can_shelve',
            'can_unshelve',
            'allowed_actions',
            'validate_token',
        ]:
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

    @action(detail=True)
    def can_ack(self, request, pk=None):
        """ Check if the user has acknowledge permissions """
        user = self.get_object()
        response = False
        if user.has_perm('tickets.acknowledge_ticket'):
            response = True
        return Response(response)

    @action(detail=True)
    def can_shelve(self, request, pk=None):
        """ Check if the user has shelve permissions """
        user = self.get_object()
        response = False
        if user.has_perm('tickets.add_shelveregistry'):
            response = True
        return Response(response)

    @action(detail=True)
    def can_unshelve(self, request, pk=None):
        """ Check if the user has unshelve permissions """
        user = self.get_object()
        response = False
        if user.has_perm('tickets.unshelve_shelveregistry'):
            response = True
        return Response(response)

    @action(detail=True)
    def allowed_actions(self, request, pk=None):
        """ Returns a dictionary with users permissions:
        ack, shelve, unshelve """
        user = self.get_object()
        response = {
            'can_ack': user.has_perm('tickets.acknowledge_ticket'),
            'can_shelve': user.has_perm('tickets.add_shelveregistry'),
            'can_unshelve': user.has_perm('tickets.unshelve_shelveregistry'),
        }
        return Response(response)

    @action(detail=False)
    def validate_token(self, request):
        """ Validates the token and returns 2 dictionaries: user data and
        users permissions (ack, shelve, unshelve) """
        user = request.user
        user_data = LoginUserSerializer(user).data
        response = {
            'user_data': user_data,
            'allowed_actions': {
                'can_ack': user.has_perm('tickets.acknowledge_ticket'),
                'can_shelve': user.has_perm('tickets.add_shelveregistry'),
                'can_unshelve':
                user.has_perm('tickets.unshelve_shelveregistry')
            }
        }
        return Response(response)


class LoggedObtainAuthToken(ObtainAuthToken):
    """ API endpoint to obtain authorization tokens """

    def post(self, request, *args, **kwargs):
        """ Handle post requests """
        try:
            token_str = super().post(request, *args, **kwargs).data['token']
        except DRFValidationError as e:
            print(type(e), e)
            raise

        token = Token.objects.get(key=token_str)
        user = token.user
        user_data = LoginUserSerializer(user).data

        return Response({
            'token': token.key,
            'user_data': user_data,
            'allowed_actions': {
                'can_ack': user.has_perm('tickets.acknowledge_ticket'),
                'can_shelve': user.has_perm('tickets.add_shelveregistry'),
                'can_unshelve':
                user.has_perm('tickets.unshelve_shelveregistry')
            }
        })
