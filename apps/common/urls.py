from django.urls import path
from apps.common import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/api-key/", views.generate_api_key, name="generate_api_key"),
    path("logout/", views.logout, name="logout"),
]
