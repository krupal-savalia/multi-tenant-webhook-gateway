import json
import secrets
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from apps.endpoints.models import WebhookEndpoint
from apps.tenants.models import Tenant
from apps.endpoints.serializers import EndPointSerializer

@require_http_methods(["GET", "POST"])
def manageEndpoints(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error":"Unauthorised operation."}, status=403)
    try:
        tenant = get_object_or_404(Tenant, owner=request.user)
    except Exception:
        return JsonResponse({"error": "User does not have a tenant."}, status=400)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

        serializer =  EndPointSerializer(data=payload)

        if not serializer.is_valid():
            return JsonResponse(
                {"error": "Please provide a valid Endpoint URL."},
                status=400,
            )
                        
        secret = "whsec_" + secrets.token_urlsafe(32)
        WebhookEndpoint.objects.create(
            tenant=tenant,
            target_url=serializer.validated_data["target_url"],
            subscribed_events=serializer.validated_data["subscribed_events"],
            secret=secret,
        )

        return JsonResponse(
            {
                "status": "created",
                "secret": secret,
                "message": "Store this secret securely. It will not be shown again.",
            },
            status=201,
        )
        
    elif request.method == "GET":
        cache_key = f"tenant_endpoints:{tenant.id}"
        data = cache.get(cache_key)
        if data is None:
            urls = WebhookEndpoint.objects.filter(tenant=tenant, is_active=True)
            data = [
                {"id": ep.id,
                "target_url": ep.target_url,
                "is_active": ep.is_active,
                "subscribed_events": ep.subscribed_events,}
                for ep in urls]
            cache.set(cache_key, data, timeout=60)

        return JsonResponse({"endpoints":data}, status=200)

@require_http_methods(["DELETE"])
def delete_endpoint(request, endpoint_id):

    if not request.user.is_authenticated:
            return JsonResponse({"error":"Authentication required."}, status=401)
    try:
        tenant = get_object_or_404(Tenant, owner=request.user) 
    except tenant.DoesNotExist:
        return JsonResponse({"error": "User does not have a tenant."}, status=400)

    endpoint = WebhookEndpoint.objects.filter(id=endpoint_id, tenant=tenant).first()

    if endpoint is None:
        return JsonResponse({"error":"Endpoint not found."}, status=404)

    endpoint.is_active = False
    endpoint.save(update_fields=["is_active", "updated_at"])

    return JsonResponse({"status":"deleted", "endpoint_id": str(endpoint.id),}, status=200)