"""
IP check module: get client IP (Streamlit/headers) and location (city) for an IP.
Uses ipinfo package when available; falls back to ipinfo.io HTTP API.
"""

from typing import Optional

# Skip these when treating as "no IP" or "no location"
_EMPTY_IP = ("127.0.0.1", "localhost", "::1", "unknown", "undefined", "none", "—")


def get_client_ip() -> Optional[str]:
    """Get client IP from Streamlit context or request headers (case-insensitive)."""
    try:
        import streamlit as _st
        if hasattr(_st, "context") and hasattr(_st.context, "ip_address"):
            ip = getattr(_st.context, "ip_address", None)
            if ip and str(ip).strip() and str(ip).lower() not in _EMPTY_IP:
                return str(ip).strip()
    except Exception:
        pass
    try:
        import streamlit as _st
        if hasattr(_st, "request") and _st.request and hasattr(_st.request, "headers"):
            headers = _st.request.headers
            header_keys_lower = {k.lower(): k for k in headers} if hasattr(headers, "keys") else {}
            for want in ("x-forwarded-for", "x-real-ip", "x-client-ip"):
                key = header_keys_lower.get(want) or want
                val = headers.get(key) if hasattr(headers, "get") else (headers[key] if key in headers else None)
                if val and isinstance(val, str) and val.strip():
                    ip = val.strip().split(",")[0].strip()
                    if ip.lower() not in _EMPTY_IP:
                        return ip
    except Exception:
        pass
    return None


def get_location(ip: Optional[str]) -> str:
    """Get city/location string for IP. Uses ipinfo package or ipinfo.io HTTP fallback."""
    s = (ip or "").strip().lower()
    if not s or s in _EMPTY_IP:
        return "Local" if ip and "127" in str(ip) else "Unknown"

    # Prefer ipinfo package (optional token from env/secrets)
    try:
        import ipinfo
        import os
        token = os.environ.get("IPINFO_TOKEN", "") or None
        try:
            import streamlit as _st
            token = token or _st.secrets.get("IPINFO_TOKEN") or None
        except Exception:
            pass
        handler = ipinfo.getHandler(token) if token else ipinfo.getHandler()
        details = handler.getDetails(ip)
        if details and hasattr(details, "city"):
            parts = [getattr(details, "city", None), getattr(details, "region", None), getattr(details, "country", None)]
            parts = [p for p in parts if p]
            return ", ".join(parts) if parts else (getattr(details, "loc", None) or "Unknown")
    except Exception:
        pass

    # Fallback: ipinfo.io HTTP API (no token)
    try:
        import urllib.request
        import json
        url = f"https://ipinfo.io/{ip}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "StreamlitApp/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            city = data.get("city") or ""
            region = data.get("region") or ""
            country = data.get("country") or ""
            parts = [p for p in (city, region, country) if p]
            return ", ".join(parts) if parts else data.get("loc", "Unknown")
    except Exception:
        return "Unknown"
