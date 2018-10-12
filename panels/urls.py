from rest_framework.routers import DefaultRouter
from panels.views import FileViewSet, AlarmConfigViewSet, PlacemarkViewSet


router = DefaultRouter()
router.register('files', FileViewSet)
router.register('alarms-config', AlarmConfigViewSet)
router.register('placemark', PlacemarkViewSet)
urlpatterns = router.urls
