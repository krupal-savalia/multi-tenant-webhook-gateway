import hashlib
import secrets
import hmac
from typing import Tuple
from django.core.cache import cache
from apps.tenants.models import Tenant


def api_key_generator() -> Tuple[str, str, str]:
    raw_key = 'wh_live_' + secrets.token_urlsafe(24) + "slug"

    api_key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest() 

    api_key_prefix = raw_key[:12]

    return api_key_hash, api_key_prefix, raw_key

def authenticate_api_key(api_key):
    if not api_key:
        return None
    
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    cache_key = f"tenant_api_key:{key_hash}"
    tenant = cache.get(cache_key)

    if tenant is None:
        for tenant in Tenant.objects.filter(is_active=True):
            if hmac.compare_digest(tenant.api_key_hash, key_hash):
                cache.set(cache_key, tenant, timeout=300)
                return tenant
    else:
        return tenant
    