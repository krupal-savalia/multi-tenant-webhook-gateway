import hmac
import hashlib
import time
import json

def generate_signature_header(secret: str, payload: dict) -> str:

    timestamp = int(time.time())

    raw_body = json.dump(payload, separators=(',', ':'))

    signed_payload = f"{timestamp}.{raw_body}".encode("utf-8")
    secret_byte = secret.encode("utf-8") 
    signature = hmac.new(secret_byte, signed_payload, hashlib.sha256).hexdigest()

    return f"t={timestamp},v1={signature}"  
    