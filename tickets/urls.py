from rest_framework.routers import DefaultRouter
from tickets.views import TicketViewSet, ShelveRegistryViewSet


router = DefaultRouter()
router.register('tickets', TicketViewSet)
router.register('shelve-registries', ShelveRegistryViewSet)
urlpatterns = router.urls
