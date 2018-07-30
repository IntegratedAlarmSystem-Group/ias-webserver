from rest_framework.routers import DefaultRouter
from panels.views import FileViewSet


router = DefaultRouter()
router.register('files', FileViewSet)
urlpatterns = router.urls
