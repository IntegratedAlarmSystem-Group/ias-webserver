from rest_framework.routers import DefaultRouter
from panels.views import PlacemarkViewSet
from panels.views import FileViewSet, LocalAlarmConfigViewSet

router = DefaultRouter()
router.register('placemark', PlacemarkViewSet)
router.register('files', FileViewSet, 'files')
router.register(
    'localalarms-config', LocalAlarmConfigViewSet, 'localalarms-config')
urlpatterns = router.urls
