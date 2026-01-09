"""
Admin utilities: visitor logging (IP, city, timestamp), save uploads, list data for admin panel.
Uses /tmp for storage so it works on Streamlit Cloud (data may not persist across restarts).
"""

import os
import csv
import time
from pathlib import Path
from typing import Optional

# Storage under /tmp for deployed apps (Streamlit Cloud)
BASE_DIR = Path(os.environ.get("ADMIN_DATA_DIR", "/tmp"))
VISITOR_LOG = BASE_DIR / "sentiment_visitor_log.csv"
UPLOADS_DIR = BASE_DIR / "sentiment_uploads"


def _ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _request_meta() -> dict:
    """Build a request META-like dict from Streamlit request for ipware."""
    meta = {}
    try:
        import streamlit as _st
        if hasattr(_st, "context") and hasattr(_st.context, "ip_address"):
            ip = getattr(_st.context, "ip_address", None)
            if ip and str(ip).strip():
                meta["REMOTE_ADDR"] = str(ip).strip()
        if hasattr(_st, "request") and _st.request and hasattr(_st.request, "headers"):
            headers = _st.request.headers
            if hasattr(headers, "keys"):
                for k in headers.keys():
                    key = k if isinstance(k, str) else str(k)
                    val = headers.get(k) if hasattr(headers, "get") else headers[k]
                    if val is None or not isinstance(val, str):
                        continue
                    val = val.strip()
                    if not val:
                        continue
                    meta[key] = val
                    meta[key.upper().replace("-", "_")] = val
                    if not key.startswith("HTTP_"):
                        meta["HTTP_" + key.upper().replace("-", "_")] = val
    except Exception:
        pass
    return meta


def get_client_ip() -> Optional[str]:
    """Get client IP using python-ipware (Streamlit request → meta → ipware)."""
    try:
        from python_ipware import IpWare
        meta = _request_meta()
        if not meta:
            print("[admin_utils] get_client_ip: no meta, IP unknown")
            return None
        client_ip, _ = IpWare().get_client_ip(meta)
        if client_ip is not None:
            s = str(client_ip).strip()
            if s and s.lower() not in ("undefined", "none"):
                print(f"[admin_utils] get_client_ip: {s}")
                return s
        print("[admin_utils] get_client_ip: ipware returned None, IP unknown")
    except Exception as e:
        print(f"[admin_utils] get_client_ip: error — {e}")
    return None


def get_ip_location(ip: Optional[str]) -> str:
    """Get city/location string for IP using ipinfo.io (no token needed for basic)."""
    s = (ip or "").strip().lower()
    if not s or s in ("127.0.0.1", "localhost", "::1", "unknown", "undefined", "none", "—"):
        return "Local" if ip and "127" in str(ip) else "Unknown"
    try:
        import urllib.request
        url = f"https://ipinfo.io/{ip}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "StreamlitApp/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            import json
            data = json.loads(resp.read().decode())
            city = data.get("city") or ""
            region = data.get("region") or ""
            country = data.get("country") or ""
            parts = [p for p in (city, region, country) if p]
            return ", ".join(parts) if parts else data.get("loc", "Unknown")
    except Exception:
        return "Unknown"


def log_visitor():
    """Append current visitor IP, location, and timestamp to log. Call once per session."""
    ip = get_client_ip()
    if ip is None or not str(ip).strip() or str(ip).lower() in ("undefined", "none"):
        ip = "—"
    city = get_ip_location(ip)
    if not city or str(city).lower() in ("undefined", "none"):
        city = "—"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    _ensure_dirs()
    file_exists = VISITOR_LOG.exists()
    with open(VISITOR_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["timestamp", "ip", "city"])
        w.writerow([timestamp, ip, city])


def save_upload(uploaded_file, original_name: str) -> str:
    """Save a copy of uploaded file to admin storage. Returns stored filename."""
    _ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in original_name)
    stored_name = f"{safe_name}_{int(time.time())}"
    path = UPLOADS_DIR / stored_name
    path.write_bytes(uploaded_file.getvalue())
    return stored_name


def get_visitor_log() -> list:
    """Return list of dicts: timestamp, ip, city. Normalizes missing/undefined to —."""
    if not VISITOR_LOG.exists():
        return []
    rows = []
    place = "—"
    with open(VISITOR_LOG, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            normalized = {
                "timestamp": (row.get("timestamp") or "").strip() or place,
                "ip": (row.get("ip") or "").strip() or place,
                "city": (row.get("city") or "").strip() or place,
            }
            if normalized["ip"].lower() in ("undefined", "unknown", "none"):
                normalized["ip"] = place
            if normalized["city"].lower() in ("undefined", "unknown", "none"):
                normalized["city"] = place
            rows.append(normalized)
    return rows


def get_uploaded_files() -> list:
    """Return list of (filename, path) for admin download."""
    _ensure_dirs()
    if not UPLOADS_DIR.exists():
        return []
    return [(p.name, p) for p in sorted(UPLOADS_DIR.iterdir(), key=lambda x: -x.stat().st_mtime)]
