from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from alarms.consumers import CoreConsumer, RequestConsumer, NotifyConsumer

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    "websocket": URLRouter([
        url("^requests/?$", RequestConsumer),
        url("^notify/?$", NotifyConsumer),
        url("^core/?$", CoreConsumer),
    ]),

})
