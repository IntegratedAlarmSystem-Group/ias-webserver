from channels.routing import route_class
from .consumers import AlarmDemultiplexer


channel_routing = [
    route_class(AlarmDemultiplexer, path='^/stream/?$'),
]
