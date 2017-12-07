from channels.routing import route_class
from .consumers import AlarmDemultiplexer
from .consumers import CoreConsumer


channel_routing = [
    route_class(AlarmDemultiplexer, path='^/stream/?$'),
    route_class(CoreConsumer, path='^/core/?$')
]
