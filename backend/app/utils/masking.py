"""Mask sensitive header values before storing."""

SENSITIVE_HEADERS = {
    "authorization",
    "x-api-key",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "proxy-authorization",
}


def mask_headers(headers: dict | None) -> dict | None:
    if not headers:
        return headers
    return {
        k: "***MASKED***" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }
