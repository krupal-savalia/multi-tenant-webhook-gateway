import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.events.models import IncomingEvent
from apps.endpoints.models import WebhookEndpoint
from apps.tenants.services import authenticate_api_key


@csrf_exempt
@require_http_methods(["POST"])
def recieve_incoming_Event(request):
    api_key = request.headers.get("X-API-Key")
    tenant = authenticate_api_key(api_key)
    if tenant == None:
        return JsonResponse({"error":"Invalid API key."}, status=401)

    event_type = request.headers.get("X-Event-Type")
    if not event_type:
        return JsonResponse({"error":"X-Event-Type header is required"}, status=400) 
    
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return JsonResponse({"error":"Idempotency-Key header is required"}, status=400)
    if len(idempotency_key) > 200:
        return JsonResponse({"error":"Idempotency-key length should be less then 200."})
        
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
             return JsonResponse({"error":"Request body must a JSON object"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error":"Request body must contain valid JSON"}, status=400)    
    
    if IncomingEvent.objects.filter(tenant=tenant, idempotency_key=idempotency_key).exists():
            return JsonResponse({"status": "already recived"}, status=200)
    
    target_url = request.headers.get("X-Endpoint")
    endpoints = WebhookEndpoint.objects.filter(tenant=tenant, is_active=True)
    if target_url:
        endpoints = endpoints.filter(target_url=target_url) 

    matching_endpoints = [ep for ep in endpoints
                          if "*" in ep.subscribed_events or event_type in ep.subscribed_events] 
        
    if not matching_endpoints:
        return JsonResponse({"error":"No active endpoint is subscribed to this event."}, status=400)

    event = IncomingEvent.objects.create(
        tenant=tenant,
        event_type = event_type,
        idempotency_key =idempotency_key,
        payload=payload,
    )

    for ep in matching_endpoints:
        pass

    return JsonResponse({"status":"accepted", "event_id": event.id, "dispatched_endpoints":len(matching_endpoints)}, status=202)