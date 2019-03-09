"""
Routing configuration of the ias_webserver project.
"""
from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from alarms.consumers import CoreConsumer, ClientConsumer
from alarms.auth import TokenAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        url("^stream/?$", TokenAuthMiddleware(ClientConsumer)),
        url("^core/?$", TokenAuthMiddleware(CoreConsumer)),
    ]),
})
