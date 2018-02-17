from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from alarms.consumers import CoreConsumer, ClientConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        url("^stream/?$", ClientConsumer),
        url("^core/?$", CoreConsumer),
    ]),
})
