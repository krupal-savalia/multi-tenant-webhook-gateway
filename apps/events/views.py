import json
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.events.models import IncomingEvent
from apps.endpoints.models import WebhookEndpoint
from apps.deliveries.models import DeliveryAttempt
from apps.deliveries.tasks import deliver_webhook
from apps.tenants.services import authenticate_api_key

idempotecy_ttl = 60 * 60 * 24

@csrf_exempt
@require_http_methods(["POST"])
def recieve_incoming_event(request):
    api_key = request.headers.get("X-API-Key")
    tenant = authenticate_api_key(api_key)
    if tenant is None:
        return JsonResponse({"error":"Invalid API key."}, status=401)

    event_type = request.headers.get("X-Event-Type")
    if not event_type:
        return JsonResponse({"error":"X-Event-Type header is required"}, status=400) 
    
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return JsonResponse({"error":"Idempotency-Key header is required"}, status=400)
    if len(idempotency_key) > 200:
        return JsonResponse({"error":"Idempotency-key length should be less then 200."}, status=400)

    cache_key = f"idem:{tenant.id}:{idempotency_key}"
    event_cache = cache.get(cache_key)
    if event_cache: 
        return JsonResponse({"status": "already recived"}, status=200)
    else:
        if IncomingEvent.objects.filter(tenant=tenant, idempotency_key=idempotency_key).exists():
            cache.set(cache_key, "1", timeout=idempotecy_ttl)
            return JsonResponse({"status": "already recived"}, status=200)
    
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
             return JsonResponse({"error":"Request body must a JSON object"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Request body must contain valid JSON"}, status=400)    
    
    target_url = request.headers.get("X-Endpoint")
    endpoints = WebhookEndpoint.objects.filter(tenant=tenant, is_active=True)
    if target_url:
        endpoints = endpoints.filter(target_url=target_url) 

    matching_endpoints = [ep 
                          for ep in endpoints
                          if (subscribed := ep.subscribed_events or [])
                          and ("*" in subscribed or event_type in subscribed)] 
        
    if not matching_endpoints:
        return JsonResponse({"error":"No active endpoint is subscribed to this event."}, status=400)

    try:
        with transaction.atomic():
            

            event = IncomingEvent.objects.create(
                tenant=tenant,
                event_type = event_type,
                idempotency_key =idempotency_key,
                payload=payload,
            )

            attempts = [
                DeliveryAttempt(
                    tenant=tenant, 
                    event=event, 
                    endpoint=endpoint,
                    attempt_number = 0
                )
                for endpoint in matching_endpoints
            ]

            DeliveryAttempt.objects.bulk_create(attempts)

            attempt_ids = [str(attempt.id) for attempt in attempts]

            def webhook_and_cache():
                for attempt_id in attempt_ids:
                    deliver_webhook.delay(attempt_id)

                cache.set(cache_key, "1", timeout=idempotecy_ttl)     

            transaction.on_commit(webhook_and_cache)

    except IntegrityError:
        existing_event = IncomingEvent.objects.get(tenant=tenant, idempotency_key=idempotency_key) 
        return JsonResponse({
            "status": "already_received",
            "event_id": str(existing_event.id),
        }, status=200)
    
    return JsonResponse({"status":"accepted", "event_id": str(event.id), "dispatched_endpoints":len(matching_endpoints)}, status=202)