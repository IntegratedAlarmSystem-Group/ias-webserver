from django.conf.urls import url
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet


router = DefaultRouter()
router.register('users', UserViewSet)
urlpatterns = router.urls
urlpatterns.append(
    url(r'^api-token-auth/', views.obtain_auth_token, name='get-token')
)
