from django.contrib import admin
from django.urls import path, include
from pto import urls as pto_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(pto_urls)),
]