from django.db import models
from apps.common.models import BaseModel


class IncomingEvent(BaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=100)
    idempotency_key = models.CharField(max_length=255)
    payload = models.JSONField()

    class Meta(BaseModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "idempotency_key"],
                name="unique_tenant_idempotency_key",
            )
        ] 

        indexes = [models.Index(fields=["tenant", "event_type", "-created_at"])]

    def __str__(self):
        return f"{self.tenant} {self.event_type}"