import secrets
from django import forms
from django.contrib import auth
from django.http import JsonResponse
from apps.tenants.models import Tenant
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from apps.tenants.services import api_key_generator
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

def home(request):
    return render(request, "home.html")

def register(request):
    if request.user.is_authenticated:    
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
        else:
            form = RegistrationForm()
            context = {
                "msg": "Please enter Unique Username and Strong Password.",
                "regform": form
                }            
            return render(request, "register.html", context)
    else:
        form = RegistrationForm()
        context = {
            "regform" : form
        }
        return render(request, "register.html", context)    

def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
            return redirect("dashboard")
        else:
            context = {
                "msg": "Please enter valid usename and password.",
                "loginform": form
            }
            return render(request, "login.html", context)
    else:
        form = AuthenticationForm()
        context  = {
            "loginform": form
        }
        return render(request, "login.html", context)

def logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
        return redirect("login")
    else:
        return redirect("login")    


#Dashboard

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    try:
        tenant = Tenant.objects.get(name=request.user.username)
    except:
        tenant = None

    return render(request, "dashboard.html", {"tenant": tenant})


#API Key Creation

@require_POST
def generate_api_key(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    key_hash, key_prefix, raw_key = api_key_generator()
    slug = "tenant-" + secrets.token_hex(4)
    tenant, _ = Tenant.objects.get_or_create(
        owner=request.user,
        defaults={
            "name": f"{request.user.username}",
            "slug": f"{slug}",
            "api_key_hash": key_hash,
            "api_key_prefix": key_prefix,
        },
    )

    tenant.api_key_hash = key_hash
    tenant.api_key_prefix = key_prefix
    tenant.save(update_fields=["api_key_hash", "api_key_prefix", "updated_at"])

    return JsonResponse({"api_key": raw_key, "api_key_prefix": key_prefix})

