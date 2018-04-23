from rest_framework.routers import DefaultRouter
from cdb.views import IasViewSet, IasioViewSet


router = DefaultRouter()
router.register('ias', IasViewSet)
router.register('iasio', IasioViewSet)
urlpatterns = router.urls
