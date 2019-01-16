from django.contrib import admin
from panels.models import (
    View, Type, AlarmConfig, Placemark, PlacemarkType, PlacemarkGroup
)


admin.site.register(AlarmConfig)
admin.site.register(View)
admin.site.register(Type)
admin.site.register(PlacemarkType)
admin.site.register(Placemark)
admin.site.register(PlacemarkGroup)
