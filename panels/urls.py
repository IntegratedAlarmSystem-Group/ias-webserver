from rest_framework.routers import DefaultRouter
from panels.views import AlarmConfigViewSet, PlacemarkViewSet
from panels.views import LocalFileViewSet

router = DefaultRouter()
router.register('alarms-config', AlarmConfigViewSet)
router.register('placemark', PlacemarkViewSet)
router.register('localfiles', LocalFileViewSet, 'localfiles')
urlpatterns = router.urls
