from django.urls import path
from apps.endpoints import views

urlpatterns = [
    path("", views.manageEndpoints, name="endpoints"),
    path("<uuid:endpoint_id>/",views.delete_endpoint, name="endpoint_delete"),
]