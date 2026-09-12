"""Firebase Realtime Database helpers for the Smart Waste app.

Place google-services.json beside this file.
The database URL is read from that file when available.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_SERVICES_FILE = os.path.join(BASE_DIR, "google-services.json")
FALLBACK_DATABASE_URL = "https://my-iot-app-391d8-default-rtdb.firebaseio.com"


def _load_database_url():
    if os.path.exists(GOOGLE_SERVICES_FILE):
        try:
            with open(GOOGLE_SERVICES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            url = data.get("project_info", {}).get("firebase_url")
            if url:
                return url.rstrip("/")
        except Exception as exc:
            print("Could not read google-services.json:", exc)

    return FALLBACK_DATABASE_URL.rstrip("/")


DATABASE_URL = _load_database_url()


def _auth_token():
    try:
        from firebase_auth import get_id_token
        return get_id_token()
    except Exception:
        return None


def _url(path):
    path = str(path).strip("/")
    url = f"{DATABASE_URL}/{path}.json" if path else f"{DATABASE_URL}/.json"
    token = _auth_token()

    if token:
        separator = "&" if "?" in url else "?"
        url += separator + "auth=" + urllib.parse.quote(token, safe="")

    return url


def _request(method, path, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    request = urllib.request.Request(
        _url(path),
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return True, json.loads(raw) if raw else None

    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            detail = json.loads(raw) if raw else {}
            message = detail.get("error", raw or f"HTTP {exc.code}")
        except Exception:
            message = f"HTTP {exc.code}"

        return False, str(message)

    except urllib.error.URLError as exc:
        return False, f"Internet/Firebase connection error: {exc.reason}"

    except Exception as exc:
        return False, str(exc)


def set_data(path, data):
    """Replace the value at a database path."""
    return _request("PUT", path, data)


def update_data(path, data):
    """Update selected fields at a database path."""
    return _request("PATCH", path, data)


def get_data(path):
    """Read a value from a database path."""
    return _request("GET", path)


def delete_data(path):
    """Delete a value from a database path."""
    return _request("DELETE", path)


def update_location(latitude, longitude, user_id="staff_1"):
    """Save the latest staff GPS position."""
    user_id = user_id or "staff_1"

    from datetime import datetime, timezone

    payload = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return update_data(f"staff_locations/{user_id}", payload)


def get_location(user_id="staff_1"):
    """Return (latitude, longitude) or (None, None)."""
    ok, result = get_data(f"staff_locations/{user_id}")

    if not ok or not isinstance(result, dict):
        return None, None

    try:
        return float(result["latitude"]), float(result["longitude"])
    except (KeyError, TypeError, ValueError):
        return None, None
