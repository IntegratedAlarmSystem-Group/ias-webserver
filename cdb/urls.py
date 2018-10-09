from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from cdb.views import retrieve_ias


urlpatterns = [url(r'^retrieve_ias/$', retrieve_ias, name="retrieve-ias")]
urlpatterns = format_suffix_patterns(urlpatterns)
