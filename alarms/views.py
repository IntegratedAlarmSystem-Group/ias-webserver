from django.shortcuts import render
from .models import Alarm


# Create your views here.
def index(request):
    """
    Root page view. Just shows a list of alarms currently available.
    """
    return render(request, "index.html", {
        "integer_values": Alarm.objects.order_by("id"),
    })
