from rest_framework.routers import DefaultRouter
from tickets.views import TicketViewSet


router = DefaultRouter()
router.register('tickets', TicketViewSet)
urlpatterns = router.urls
