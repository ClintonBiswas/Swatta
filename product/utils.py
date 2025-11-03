from django.core.signing import Signer, BadSignature
import requests
import uuid
from django.conf import settings
import hashlib
import time

BANGLA_TO_ENGLISH_DIGIT = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
signer = Signer()

def normalize_phone(phone):
    """Convert Bangla digits to English and clean phone number"""
    if not phone:
        return ""
    phone = str(phone).translate(BANGLA_TO_ENGLISH_DIGIT)
    digits = ''.join(c for c in phone if c.isdigit())
    return digits[-11:] if digits else ""

def get_guest_phone_from_cookie(request):
    """Safely get and verify guest phone from cookie"""
    cookie_value = request.COOKIES.get('guest_phone')
    if not cookie_value:
        return None
    try:
        return signer.unsign(cookie_value)
    except BadSignature:
        return None
    


PIXEL_ID = settings.FACEBOOK_PIXEL_ID
ACCESS_TOKEN = settings.FACEBOOK_ACCESS_TOKEN
API_VERSION = settings.FACEBOOK_API_VERSION

def hash_data(data):
    """Return SHA256 hash for a single string (or None)."""
    return hashlib.sha256(data.strip().lower().encode()).hexdigest() if data else None

def _ensure_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return [v for v in val if v is not None and v != ""]
    return [val]

def normalize_user_data(user_data):
    """
    Accepts user_data like {"em":[...], "ph":[...], "fbc": "...", ...}
    Hashes em and ph automatically. Leaves fbc/fbp/fn/ip/ua untouched.
    """
    if not user_data:
        return {}

    normalized = {}
    for k, vals in user_data.items():
        if vals is None or vals == []:
            continue

        # emails & phones: ensure list and hash each value
        if k in ("em", "ph"):
            values = _ensure_list(vals)
            hashed = [hash_data(v) for v in values if v]
            if hashed:
                normalized[k] = hashed
        # pass-through single or list values (fbc, fbp, fn, client_ip_address, client_user_agent)
        elif k in ("fbc", "fbp", "fn", "client_ip_address", "client_user_agent"):
            # keep as-is (string or list) but normalize to string if single-element list
            if isinstance(vals, (list, tuple)) and len(vals) == 1:
                normalized[k] = vals[0]
            else:
                normalized[k] = vals
        else:
            # fallback - keep other fields untouched
            normalized[k] = vals
    return normalized

def send_event(event_name, user_data=None, custom_data=None, test_event_code=None, event_id=None):
    """
    Send event to Meta Conversions API and return generated or provided event_id.
    """
    api_url = f"https://graph.facebook.com/{API_VERSION}/{PIXEL_ID}/events"
    # use provided event_id or generate one
    event_id = event_id or str(uuid.uuid4())

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(time.time()),
                "event_id": event_id,
                "action_source": "website",
                "user_data": normalize_user_data(user_data or {}),
                "custom_data": custom_data or {}
            }
        ],
        "access_token": ACCESS_TOKEN
    }

    if test_event_code:
        payload["test_event_code"] = test_event_code

    try:
        r = requests.post(api_url, json=payload, timeout=6)
        r.raise_for_status()
    except Exception as e:
        print(f"[CAPI ERROR] event={event_name} id={event_id} err={str(e)} payload={payload}")
    return event_id





