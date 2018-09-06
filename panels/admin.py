from django.contrib import admin
from panels.models import File, View, Type, AlarmConfig

admin.site.register(File)
admin.site.register(AlarmConfig)
admin.site.register(View)
admin.site.register(Type)
