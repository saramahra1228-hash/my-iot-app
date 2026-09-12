"""Firebase Authentication REST helper for Smart Waste Monitor.

This module contains no Kivy UI code. Network calls are synchronous by design;
the login screen runs them in a background thread so the Kivy UI never freezes.
"""

import json
import os
import urllib.error
import urllib.request


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_SERVICES_FILE = os.path.join(BASE_DIR, "google-services.json")


def _load_firebase_settings():
    if not os.path.exists(GOOGLE_SERVICES_FILE):
        raise FileNotFoundError(
            f"google-services.json not found: {GOOGLE_SERVICES_FILE}"
        )

    with open(GOOGLE_SERVICES_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    project_id = cfg.get("project_info", {}).get("project_id")
    clients = cfg.get("client") or []
    api_key = None

    for client in clients:
        for key in client.get("api_key", []) or []:
            api_key = key.get("current_key")
            if api_key:
                break
        if api_key:
            break

    if not api_key:
        raise ValueError("Firebase Web API key was not found in google-services.json")

    return api_key, project_id


try:
    FIREBASE_API_KEY, FIREBASE_PROJECT_ID = _load_firebase_settings()
    _CONFIG_ERROR = ""
except Exception as exc:
    FIREBASE_API_KEY = ""
    FIREBASE_PROJECT_ID = ""
    _CONFIG_ERROR = str(exc)


# Current authenticated Firebase session.
ID_TOKEN = None
REFRESH_TOKEN = None
LOCAL_ID = None
EMAIL = None


def _friendly_error(data):
    code = ((data or {}).get("error") or {}).get("message", "")
    messages = {
        "EMAIL_EXISTS": "This email address is already registered.",
        "EMAIL_NOT_FOUND": "No account exists with this email address.",
        "INVALID_PASSWORD": "Incorrect password.",
        "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
        "USER_DISABLED": "This account has been disabled.",
        "INVALID_EMAIL": "Please enter a valid email address.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please try again later.",
        "WEAK_PASSWORD : Password should be at least 6 characters": "Password must be at least 6 characters.",
    }
    return messages.get(code, code.replace("_", " ").title() if code else "Firebase request failed.")


def _post(endpoint, payload):
    if _CONFIG_ERROR:
        return False, f"Firebase configuration error: {_CONFIG_ERROR}"

    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"{endpoint}?key={FIREBASE_API_KEY}"
    )

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read().decode("utf-8")
            return True, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        return False, _friendly_error(data)
    except urllib.error.URLError as exc:
        return False, "Network error. Check your internet connection and try again."
    except TimeoutError:
        return False, "Firebase request timed out. Please try again."
    except Exception as exc:
        return False, f"Firebase error: {exc}"


def login_user(email, password):
    """Sign in with Firebase email/password authentication."""
    global ID_TOKEN, REFRESH_TOKEN, LOCAL_ID, EMAIL

    email = (email or "").strip()
    password = password or ""

    if not email:
        return False, "Email address daalein."
    if not password:
        return False, "Password daalein."

    ok, result = _post(
        "accounts:signInWithPassword",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )

    if not ok:
        return False, result

    ID_TOKEN = result.get("idToken")
    REFRESH_TOKEN = result.get("refreshToken")
    LOCAL_ID = result.get("localId")
    EMAIL = result.get("email", email)

    if not ID_TOKEN or not LOCAL_ID:
        logout_user()
        return False, "Firebase returned an incomplete login response."

    return True, result


def signup_user(email, password):
    """Create a Firebase email/password account."""
    global ID_TOKEN, REFRESH_TOKEN, LOCAL_ID, EMAIL

    email = (email or "").strip()
    password = password or ""

    ok, result = _post(
        "accounts:signUp",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )

    if not ok:
        return False, result

    ID_TOKEN = result.get("idToken")
    REFRESH_TOKEN = result.get("refreshToken")
    LOCAL_ID = result.get("localId")
    EMAIL = result.get("email", email)
    return True, result


def send_password_reset_email(email):
    email = (email or "").strip()
    if not email:
        return False, "Email address daalein."

    ok, result = _post(
        "accounts:sendOobCode",
        {
            "requestType": "PASSWORD_RESET",
            "email": email,
        },
    )
    return ok, result if ok else result


def get_id_token():
    return ID_TOKEN


def get_current_user():
    if not LOCAL_ID:
        return None
    return {
        "localId": LOCAL_ID,
        "email": EMAIL,
        "idToken": ID_TOKEN,
        "refreshToken": REFRESH_TOKEN,
    }


def logout_user():
    global ID_TOKEN, REFRESH_TOKEN, LOCAL_ID, EMAIL
    ID_TOKEN = None
    REFRESH_TOKEN = None
    LOCAL_ID = None
    EMAIL = None
