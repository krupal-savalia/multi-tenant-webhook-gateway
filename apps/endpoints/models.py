from django.db import models
from apps.common.models import BaseModel
from apps.tenants.models import Tenant
from apps.common.validators import validated_target_url


class WebhookEndpoint(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="endpoints")
    target_url = models.URLField(max_length=2048, validators=[validated_target_url])
    secret = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True, db_index=True)
    subscribed_events = models.JSONField(default=list)
    failure_count = models.PositiveIntegerField(default=0)
    circuit_broken_until = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["tenant","is_active"])]

    def __str__(self):
        return f"{self.tenant.name} -> {self.target_url} -> {self.is_active}"