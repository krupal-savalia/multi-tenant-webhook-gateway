from django.db import models
from apps.common.models import BaseModel
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class RateLimitTire(models.TextChoices):
    FREE = "free", _("Free (60 req/min)")
    PRO = "pro", _("Pro (600 req/min)")
    ENTERPRISE = "enterprise", _("Enterprise (6000 req/min)")


class Tenant(BaseModel):
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="tenant",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    tire = models.CharField(max_length=20, choices=RateLimitTire.choices, default=RateLimitTire.FREE)
    api_key_hash = models.CharField(max_length=64, unique=True)
    api_key_prefix = models.CharField(max_length=16)


    def __str__(self):
        return f"{self.name} {self.tire}"
