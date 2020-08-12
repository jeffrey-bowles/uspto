from django.urls import path
from .views import update_patents, update_fee_events


urlpatterns = [
    path('update_patents', update_patents),
    path('update_fee_events', update_fee_events),
]
