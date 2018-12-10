from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, LoggedObtainAuthToken


router = DefaultRouter()
router.register('users', UserViewSet)
urlpatterns = router.urls
urlpatterns.append(
    url(r'^api-token-auth/', LoggedObtainAuthToken.as_view(), name='get-token')
)
urlpatterns.append(
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
)
