from django.contrib import admin
from panels.models import (
    File, View, Type, AlarmConfig, Placemark, PlacemarkType, PlacemarkGroup
)

admin.site.register(File)
admin.site.register(AlarmConfig)
admin.site.register(View)
admin.site.register(Type)
admin.site.register(PlacemarkType)
admin.site.register(Placemark)
admin.site.register(PlacemarkGroup)
