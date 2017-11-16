from django.shortcuts import render


def test_core(request):
    return render(request, "test.html")
