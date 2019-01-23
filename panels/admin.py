from django.contrib import admin
from panels.models import (
    Placemark, PlacemarkType, PlacemarkGroup
)


admin.site.register(PlacemarkType)
admin.site.register(Placemark)
admin.site.register(PlacemarkGroup)
