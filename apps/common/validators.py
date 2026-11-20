import ipaddress
import socket
from urllib.parse import urlparse
from django.core.exceptions import ValidationError


def validated_target_url(value):

    parsed = urlparse(value)

    if parsed.scheme not in {"http","https"}:
        raise ValidationError("Onaly HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValidationError("A valid hostname required.")

    if parsed.username or parsed.password:
        raise ValidationError("URLs must not contain username or password.")

    hostname = parsed.hostname.lower().rstrip(".")

    blocked_hostnames = {
        "localhost",
        "localhost.localadmin",
    }

    if hostname in blocked_hostnames:
        raise ValidationError("Internal hostnames are not allowed.")

    try:
        addresses = socket.getaddrinfo(
            hostname, None, type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        raise ValidationError("The hostname could not be resolved.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if (ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValidationError("Private or Internal network addresses are not allowed.")