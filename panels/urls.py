from rest_framework.routers import DefaultRouter
from panels.views import AlarmConfigViewSet, PlacemarkViewSet
from panels.views import FileViewSet

router = DefaultRouter()
router.register('alarms-config', AlarmConfigViewSet)
router.register('placemark', PlacemarkViewSet)
router.register('files', FileViewSet, 'files')
urlpatterns = router.urls
