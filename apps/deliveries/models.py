from django.db import models
from apps.common.models import BaseModel
from django.utils.translation import gettext_lazy as _

class DeliveryStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    EXHAUSTED = "exhausted", _("Exhausted")


class DeliveryAttempt(BaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="delivery_attempts", default="")
    endpoint = models.ForeignKey("endpoints.WebhookEndpoint", on_delete=models.CASCADE, related_name="delivery_attempts")
    event = models.ForeignKey("events.IncomingEvent", on_delete=models.CASCADE, related_name="delivery_attempts")
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    attempt_number = models.PositiveIntegerField(default=1)

    response_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    response_headers = models.JSONField(default=dict, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["tenant", "status", "-created_at"]),
            models.Index(fields=["endpoint", "status", "-created_at"]),
            models.Index(fields=["endpoint", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.endpoint} -> {self.status} -> {self.attempt_number}"