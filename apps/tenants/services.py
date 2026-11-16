import hashlib
import secrets
from typing import Tuple


def api_key_generator() -> Tuple[str, str, str]:
    raw_key = 'wh_live_' + secrets.token_urlsafe(24) + "slug"

    api_key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest() 

    api_key_prefix = raw_key[:12]

    return api_key_hash, api_key_prefix, raw_key