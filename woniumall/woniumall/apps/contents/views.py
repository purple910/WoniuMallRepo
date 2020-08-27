from django.shortcuts import render

# Create your views here.
from django.views import View


class HomeView(View):
    """首页"""

    def get(self, request):
        return render(request, "index.html")
