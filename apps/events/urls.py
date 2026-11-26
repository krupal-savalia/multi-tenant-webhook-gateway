from django.urls import path
from apps.events import views


urlpatterns = [
    path("", views.recieve_incoming_event, name="incomingEvent"),
]