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

def normalize_user_data(user_data):
    """
    Accepts user_data like {"em":[...], "ph":[...], ...}
    Hashes em and ph automatically. Leaves other fields untouched.
    """
    if not user_data:
        return {}

    normalized = {}
    for k, vals in user_data.items():
        if not vals:
            continue
        if k in ("em", "ph"):
            # ensure list and hash each
            normalized[k] = [hash_data(v) for v in vals if v]
        else:
            normalized[k] = vals
    return normalized

def send_event(event_name, user_data=None, custom_data=None, test_event_code=None):
    """
    Send event to Meta Conversions API and return generated event_id.
    Automatically hashes email & phone in user_data.
    """
    api_url = f"https://graph.facebook.com/{API_VERSION}/{PIXEL_ID}/events"
    event_id = str(uuid.uuid4())

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(time.time()),
                "event_id": event_id,
                "action_source": "website",
                "user_data": normalize_user_data(user_data),
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
        # Log the error in production logger, here a print helps debugging
        print(f"[CAPI ERROR] event={event_name} id={event_id} err={str(e)} payload={payload}")
    else:
        # Optionally print success during development
        # print(f"[CAPI SUCCESS] {event_name} -> {event_id}")
        pass

    return event_id





