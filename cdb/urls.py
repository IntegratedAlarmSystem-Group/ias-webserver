from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from cdb.views import retrieve_ias


urlpatterns = [url(r'^ias/$', retrieve_ias, name="ias")]
urlpatterns = format_suffix_patterns(urlpatterns)
