from channels.routing import route_class
from .consumers import CoreConsumer, AlarmRequestConsumer


channel_routing = [
    route_class(AlarmRequestConsumer, path='^/stream/?$'),
    route_class(CoreConsumer, path='^/core/?$')
]
