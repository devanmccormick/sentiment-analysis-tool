"""
Admin utilities: visitor logging (IP, city, timestamp), save uploads, list data for admin panel.
Uses /tmp for storage so it works on Streamlit Cloud (data may not persist across restarts).
Uses ip_check module for client IP and location.
"""

import os
import csv
import time
from pathlib import Path

from ip_check import get_client_ip, get_location

# Storage under /tmp for deployed apps (Streamlit Cloud)
BASE_DIR = Path(os.environ.get("ADMIN_DATA_DIR", "/tmp"))
VISITOR_LOG = BASE_DIR / "sentiment_visitor_log.csv"
UPLOADS_DIR = BASE_DIR / "sentiment_uploads"


def _ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def log_visitor():
    """Append current visitor IP, location, and timestamp to log. Call once per session."""
    ip = get_client_ip()
    if ip is None or not str(ip).strip() or str(ip).lower() in ("undefined", "none"):
        ip = "—"
    city = get_location(ip)
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
