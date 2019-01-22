from rest_framework.routers import DefaultRouter
from panels.views import PlacemarkViewSet
from panels.views import FileViewSet, AlarmConfigViewSet

router = DefaultRouter()
router.register('placemark', PlacemarkViewSet)
router.register('files', FileViewSet, 'files')
router.register('alarms-config', AlarmConfigViewSet, 'alarms-config')
urlpatterns = router.urls
