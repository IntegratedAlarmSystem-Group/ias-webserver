from rest_framework.routers import DefaultRouter
from panels.views import FileViewSet, AlarmConfigViewSet


router = DefaultRouter()
router.register('files', FileViewSet)
router.register('alarms-config', AlarmConfigViewSet)
urlpatterns = router.urls
