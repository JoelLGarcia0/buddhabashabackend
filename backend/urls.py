
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path("store/", include("store.urls")),
]

# Static files are handled by WhiteNoise middleware
# No need for static() URLs since no static files exist