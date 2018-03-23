from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from cdb.views import IasViewSet, IasioViewSet


router = DefaultRouter()
router.register('ias', IasViewSet)
router.register('iasio', IasioViewSet)

urlpatterns = {}
urlpatterns = format_suffix_patterns(urlpatterns)
urlpatterns += [
    path('auth/', include('rest_framework.urls', namespace='rest_framework'))
]
urlpatterns.append(path('', include(router.urls)),)
