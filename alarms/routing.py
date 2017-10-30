from channels.routing import route
channel_routing = [
    route("http.request", "alarms.consumers.http_consumer"),
]
