from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from alarms.consumers import CoreConsumer, AlarmRequestConsumer

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    "websocket": URLRouter([
        url("^stream/?$", AlarmRequestConsumer),
        url("^core/?$", CoreConsumer),
    ]),

})
