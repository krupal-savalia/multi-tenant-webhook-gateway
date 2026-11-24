import time
import httpx
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import F
from celery.utils.log import get_task_logger

from apps.deliveries.crypto import generate_signature_header
from apps.deliveries.models import DeliveryAttempt, DeliveryStatus


logger = get_task_logger(__name__)

@shared_task(
        bind=True,
        max_retries=5,
        default_retry_delay=60,
)
def deliver_webhook(self, attempt_id): 
    try:
        attempt = (
            DeliveryAttempt.objects.select_related("event", "endpoint").get(id=attempt_id)
        )
    except DeliveryAttempt.DoesNotExist:
        return f"Delivery Attempt {attempt_id} does not exist."   

    if attempt.status == DeliveryStatus.SUCCESS:
        return "Already delivered."

    endpoint = attempt.endpoint
    event = attempt.event

    if not endpoint.is_active:
        attempt.status = DeliveryStatus.FAILED
        attempt.error_message = "Endpoint is inactive."
        attempt.save(update_fields=["status", "error_message", "updated_at"])
        return "Endpoint is inactive."

    if endpoint.circuit_broken_until and endpoint.circuit_broken_until > timezone.now():
        attempt.status = DeliveryStatus.FAILED
        attempt.error_message = f"Circuit breaker open until {endpoint.circuit_broken_until}."
        attempt.save(update_fields=["status", "error_message", "updated_at"])
        return "Circuit breaker is open."
    
    attempt.status = DeliveryStatus.PENDING
    attempt.attempt_number += 1
    attempt.save(update_fields=["status", "attempt_number", "updated_at"])

    signature_header = generate_signature_header(endpoint.secret, event.payload)

    started_at = time.perf_counter()

    try:
        response = httpx.post(
            endpoint.target_url,
            json={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "payload": event.payload
            },
            headers={
                "Content-Type": "application/json",
                "X-Event-Type": event.event_type,
                "X-Event-Id": str(event.id),
                "X-Webhook-Signature": signature_header,
            },
            timeout=httpx.Timeout(
                connect=5.0,
                read=10.0,
                write=10.0,
                pool=5.0,
            ),
            follow_redirects=False,
        )

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)

        attempt.response_status_code = response.status_code
        attempt.response_body = response.text[:1000]
        attempt.response_time_ms = elapsed_ms
        attempt.response_headers = dict(response.headers)

        if 200 <= response.status_code < 300:
            attempt.status = DeliveryStatus.SUCCESS
            attempt.error_message = ""
            attempt.next_retry_at = None
            attempt.save(update_fields=[
                "status",
                "response_status_code",
                "response_body",
                "response_headers",
                "response_time_ms",
                "error_message",
                "next_retry_at",
                "updated_at",
            ])

            endpoint.failure_count = 0
            endpoint.circuit_broken_until = None
            endpoint.save(update_fields=["failure_count", "circuit_broken_until"])

            return "Webhook delivered seccessfully."

        attempt.status = DeliveryStatus.FAILED
        attempt.error_message = f"Destination returned HTTP {response.status_code}."
        attempt.save(update_fields=[
            "status",
            "response_status_code",
            "response_body",
            "response_headers",
            "response_time_ms",
            "error_message",
            "next_retry_at",
            "updated_at",
        ])

        endpoint.failure_count = F("failure_count") + 1
        endpoint.save(update_fields=["failure_count"])
        endpoint.refresh_from_db()

        if endpoint.failure_count >= 50:
            endpoint.circuit_broken_until = timezone.now() + timedelta(days=1)
            endpoint.save(update_fields=["circuit_broken_until"]) 
            logger.warning(f"Circuit breaker tripped for endpoint {endpoint.id}")
            return "Circuit breker tripped."

        if response.status_code >= 500:
            raise self.retry(
                exc=Exception(
                    f"Temporary destination error: {response.status_code}"
                ),
                countdown=10 * (2 ** self.request.retries)
            )
        
        return "Webhook delivery failed permanently."
    
    except httpx.ReadError as exc:

        elapsed_ms = int(timezone.now() - started_at) * 1000

        attempt.status = DeliveryStatus.FAILED
        attempt.error_message = str(exc)
        attempt.save()
        
        endpoint.failure_count = F("failure_count") + 1
        endpoint.save(update_fields=["failure_count"])
        endpoint.refresh_from_db()
        
        if endpoint.failure_count >= 50:
            endpoint.circuit_broken_until = timezone.now() + timedelta(days=1)
            endpoint.save(update_fields=["circuit_broken_until"]) 
            logger.warning(f"Circuit breaker tripped for endpoint {endpoint.id}")
            return "Circuit breker tripped due to timeout."

        raise self.retry(
            exc=exc,
            countdown=10 * (2 ** self.request.retries)
        )


