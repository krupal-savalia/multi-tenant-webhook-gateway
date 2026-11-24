from rest_framework.urls import path
from apps.events import views


urlpatterns = [
    path("", views.recieve_incoming_Event, name="incomingEvent"),
]