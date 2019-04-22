from django.shortcuts import render


def test_core(request):
    """ Basic view used mostly for debuging purposes """
    return render(request, "test.html")
